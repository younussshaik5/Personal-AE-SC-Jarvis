#!/usr/bin/env python3
"""
AccountWatcher — the central interlinking reactive router.

Subscribes to file.created and file.modified events from FileSystemObserver.
Looks at WHERE the file is and WHAT it is, then fires the right event so the
right component handles it.

THIS is what makes everything interlinked. One file changes → this router
fires the appropriate event → the right processor updates all related files.

Routing map:
  ACCOUNTS/{name}/MEETINGS/{file}       → meeting.recording.added (account known)
  ACCOUNTS/{name}/DOCUMENTS/{file}      → document.added
  ACCOUNTS/{name}/EMAILS/{file}         → email.added
  ACCOUNTS/{name}/meddpicc.json         → meddpicc.updated → stage evaluation
  ACCOUNTS/{name}/deal_stage.json       → deal.stage.changed → skills trigger
  ACCOUNTS/{name}/ (new dir)            → account.created → initializer
  MEETINGS/{file}                       → meeting.recording.dropped (account unknown)
  JARVIS_BRAIN.md                       → brain.modified (ConversationExtractor handles)
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event
from jarvis.utils.config import ConfigManager
from jarvis.utils.account_utils import extract_account_name

VIDEO_EXTS  = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".mp3", ".wav", ".m4a"}
DOC_EXTS    = {".pdf", ".docx", ".doc", ".txt", ".md", ".pptx", ".xlsx"}
IGNORE_NAMES = {
    "README.md", ".DS_Store", "activities.jsonl",
    "conversation_log.md", "actions.md",
    # Auto-generated files — never re-process these
    "discovery_prep.md", "final_discovery.md",
    "battlecard.md", "battlecard_data.json",
    "demo_strategy.md", "demo_script.md",
    "risk_report.md", "next_steps.md", "email_drafts.json",
    "roi_model.md", "tco_analysis.md", "value_data.json",
    "rfi_analysis.md", "rfi_responses.md",
}

# Trigger file prefix — written by MCP jarvis_trigger_skill tool
TRIGGER_PREFIX = ".jarvis_trigger_"

# Map from trigger skill name → event type + task name
TRIGGER_SKILL_MAP = {
    "battlecard":          "discovery.updated",   # reuses same pipeline as discovery update
    "discovery":           "discovery.updated",
    "demo_strategy":       "discovery.updated",
    "risk_report":         "meddpicc.updated",
    "value_architecture":  "discovery.updated",
    "proposal":            "value_architecture.updated",
    "sow":                 "proposal.generated",
    "architecture_diagram":"discovery.updated",
    "summary":             "account.initialized",
}
IGNORE_DIRS = {".git", "__pycache__", "node_modules", ".processed",
               "failed", "dist", "logs", "data", "INTEL"}

# Presales sections that can receive user-dropped files
# Files dropped here are extracted and fed to relevant downstream sections
PRESALES_SECTIONS = {
    "DISCOVERY", "RFI", "BATTLECARD", "DEMO_STRATEGY",
    "RISK_REPORT", "NEXT_STEPS", "VALUE_ARCHITECTURE"
}


class AccountWatcher:
    """
    Watches JARVIS_HOME for file changes and fires semantic events
    so all components stay in sync automatically.
    """

    def __init__(self, config_manager: ConfigManager, event_bus: EventBus):
        self.config = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("observers.account_watcher")
        self._jarvis_home: Optional[Path] = None
        self._accounts_dir: Optional[Path] = None
        self._meetings_dir: Optional[Path] = None
        self._brain_file: Optional[Path] = None

    async def start(self):
        self._jarvis_home   = Path(self.config.workspace_root)
        self._accounts_dir  = self._jarvis_home / "ACCOUNTS"
        self._meetings_dir  = self._jarvis_home / "MEETINGS"
        self._brain_file    = self._jarvis_home / "JARVIS_BRAIN.md"

        # Ensure root directories exist so FileSystemObserver can watch them
        for d in (self._accounts_dir, self._meetings_dir):
            d.mkdir(parents=True, exist_ok=True)

        self.event_bus.subscribe("file.created",  self._on_file_event)
        self.event_bus.subscribe("file.modified", self._on_file_event)

        self.logger.info("AccountWatcher started",
                         accounts=str(self._accounts_dir),
                         meetings=str(self._meetings_dir))

    async def stop(self):
        self.logger.info("AccountWatcher stopped")

    # ------------------------------------------------------------------
    # Main router
    # ------------------------------------------------------------------

    async def _on_file_event(self, event: Event):
        path_str = event.data.get("path", "")
        is_dir   = event.data.get("is_directory", False)
        evt_type = event.type  # "file.created" or "file.modified"

        path = Path(path_str)

        # Skip noise
        if self._should_ignore(path):
            return

        # ── JARVIS_BRAIN.md modified ──────────────────────────────────
        if self._brain_file and path.resolve() == self._brain_file.resolve():
            self.event_bus.publish(Event(
                type="brain.modified",
                source="account_watcher",
                data={"path": path_str}
            ))
            return

        # ── Global MEETINGS/ drop zone ────────────────────────────────
        if (self._meetings_dir
                and self._is_inside(path, self._meetings_dir)
                and not is_dir
                and evt_type == "file.created"
                and path.suffix.lower() in VIDEO_EXTS):
            self.event_bus.publish(Event(
                type="meeting.recording.dropped",
                source="account_watcher",
                data={"path": path_str, "filename": path.name}
            ))
            return

        # ── Anything inside ACCOUNTS/ ─────────────────────────────────
        if self._accounts_dir and self._is_inside(path, self._accounts_dir):
            await self._route_accounts_event(path, is_dir, evt_type)

    async def _route_accounts_event(self, path: Path, is_dir: bool, evt_type: str):
        """Route events for files/folders inside ACCOUNTS/."""
        try:
            rel = path.relative_to(self._accounts_dir)
        except ValueError:
            return

        parts = rel.parts
        if not parts:
            return

        # Validate that the first component is a real account directory (not a system folder)
        candidate = parts[0]
        account_path = self._accounts_dir / candidate
        if not account_path.is_dir():
            return
        IGNORED_SYSTEM_FOLDERS = {
            'DOCUMENTS', 'EMAILS', 'MEETINGS', 'MEMORY',
            'data', 'logs', 'recordings', '.git', '__pycache__'
        }
        if candidate in IGNORED_SYSTEM_FOLDERS:
            return
        account_name = candidate

        # ── New top-level account folder created ──────────────────────
        if is_dir and len(parts) == 1 and evt_type == "file.created":
            # Let AccountAutoInitializer handle it via file.created event
            # (already subscribed). Nothing extra to do here.
            return

        if len(parts) < 2:
            return

        sub = parts[1]   # e.g. "MEETINGS", "DOCUMENTS", "meddpicc.json"

        # ── Account MEETINGS/ — recording dropped (account already known) ──
        if (sub == "MEETINGS"
                and not is_dir
                and evt_type == "file.created"
                and path.suffix.lower() in VIDEO_EXTS):
            self.event_bus.publish(Event(
                type="meeting.recording.added",
                source="account_watcher",
                data={"path": str(path), "account": account_name,
                      "filename": path.name}
            ))
            return

        # ── Account DOCUMENTS/ — file dropped ────────────────────────
        if (sub == "DOCUMENTS"
                and not is_dir
                and evt_type == "file.created"
                and path.suffix.lower() in DOC_EXTS
                and path.name not in IGNORE_NAMES):
            self.event_bus.publish(Event(
                type="document.added",
                source="account_watcher",
                data={"path": str(path), "account": account_name,
                      "filename": path.name}
            ))
            return

        # ── Account EMAILS/ — email thread dropped ────────────────────
        if (sub == "EMAILS"
                and not is_dir
                and evt_type == "file.created"
                and path.suffix.lower() in {".md", ".txt", ".eml", ".msg"}
                and path.name not in IGNORE_NAMES):
            self.event_bus.publish(Event(
                type="email.added",
                source="account_watcher",
                data={"path": str(path), "account": account_name,
                      "filename": path.name}
            ))
            return

        # ── RFI/ — user drops an RFI document ────────────────────────────
        # Only triggers on actual source RFPs (PDFs, DOCX, TXT) — not on
        # JARVIS-generated analysis/response files (those are in IGNORE_NAMES)
        if (sub == "RFI"
                and not is_dir
                and evt_type == "file.created"
                and path.suffix.lower() in DOC_EXTS
                and path.name not in IGNORE_NAMES
                and "_filled" not in path.stem):
            self.event_bus.publish(Event(
                type="rfi.file.added",
                source="account_watcher",
                data={"path": str(path), "account": account_name,
                      "filename": path.name}
            ))
            return

        # ── Any other presales section — user drops a file ───────────
        # Extract useful data from it and cascade to relevant sections
        if (sub in PRESALES_SECTIONS
                and sub != "RFP"  # RFP handled above
                and not is_dir
                and evt_type == "file.created"
                and (path.suffix.lower() in DOC_EXTS | VIDEO_EXTS)
                and path.name not in IGNORE_NAMES):
            self.event_bus.publish(Event(
                type="presales.file.added",
                source="account_watcher",
                data={"path": str(path), "account": account_name,
                      "section": sub, "filename": path.name}
            ))
            return

        # ── meddpicc.json modified → evaluate stage advancement ───────
        if sub == "meddpicc.json" and evt_type == "file.modified":
            self.event_bus.publish(Event(
                type="meddpicc.updated",
                source="account_watcher",
                data={"account": account_name, "path": str(path)}
            ))
            return

        # ── deal_stage.json modified → trigger stage-entry skills ─────
        if sub == "deal_stage.json" and evt_type == "file.modified":
            self._trigger_stage_skills(path, account_name)
            return

        # ── .jarvis_trigger_{skill} — written by MCP jarvis_trigger_skill ──
        # Claude writes this file → we detect it → fire event → delete file
        if (sub.startswith(TRIGGER_PREFIX)
                and not is_dir
                and evt_type == "file.created"):
            skill_name = sub[len(TRIGGER_PREFIX):]
            await self._handle_skill_trigger(path, account_name, skill_name)
            return

    # ------------------------------------------------------------------
    # MCP trigger file handler
    # ------------------------------------------------------------------

    async def _handle_skill_trigger(self, trigger_path: Path, account_name: str, skill_name: str):
        """Process a .jarvis_trigger_{skill} file written by the MCP tool."""
        try:
            # Read trigger metadata
            reason = "MCP trigger"
            try:
                import json as _json
                data = _json.loads(trigger_path.read_text())
                reason = data.get("reason", reason)
            except Exception:
                pass

            # Delete the trigger file immediately to prevent re-processing
            try:
                trigger_path.unlink()
            except Exception:
                pass

            # Map skill → event type
            event_type = TRIGGER_SKILL_MAP.get(skill_name)
            if not event_type:
                self.logger.warning("Unknown trigger skill", skill=skill_name, account=account_name)
                return

            self.logger.info("Skill trigger detected",
                             account=account_name, skill=skill_name,
                             event=event_type, reason=reason)

            # Publish the event that the skill subscribes to
            self.event_bus.publish(Event(
                type=event_type,
                source="account_watcher.trigger",
                data={
                    "account": account_name,
                    "account_name": account_name,
                    "triggered_skill": skill_name,
                    "reason": reason,
                    "path": str(self._accounts_dir / account_name),
                }
            ))

            # Also publish a dedicated skill.trigger event for any generic listener
            self.event_bus.publish(Event(
                type="skill.trigger.request",
                source="account_watcher.trigger",
                data={
                    "skill": skill_name,
                    "account": account_name,
                    "reason": reason,
                }
            ))

        except Exception as e:
            self.logger.error("Failed to handle skill trigger",
                              account=account_name, skill=skill_name, error=str(e))

    # ------------------------------------------------------------------
    # Stage skills trigger
    # ------------------------------------------------------------------

    def _trigger_stage_skills(self, stage_file: Path, account_name: str):
        """Read deal_stage.json and fire appropriate skill triggers."""
        try:
            import json
            data = json.loads(stage_file.read_text())
            stage = data.get("stage", "")

            skill_map = {
                "discovery":   ["meeting_prep", "meddpicc"],
                "demo":        ["demo_strategy", "battlecards", "meeting_prep"],
                "proposal":    ["proposal_generator", "value_architecture", "risk_report"],
                "negotiation": ["risk_report", "followup_email"],
                "closed_won":  ["account_dashboard"],
                "closed_lost": ["risk_report"],
            }

            skills = skill_map.get(stage, [])
            for skill in skills:
                self.event_bus.publish(Event(
                    type="skill.trigger.request",
                    source="account_watcher",
                    data={
                        "skill": skill,
                        "account": account_name,
                        "reason": f"Deal stage changed to {stage}",
                    }
                ))

            if skills:
                self.logger.info("Stage skills triggered",
                                 account=account_name, stage=stage, skills=skills)

        except Exception as e:
            self.logger.warning("Stage skills trigger failed",
                                account=account_name, error=str(e))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _is_inside(self, path: Path, parent: Path) -> bool:
        try:
            path.resolve().relative_to(parent.resolve())
            return True
        except ValueError:
            return False

    def _should_ignore(self, path: Path) -> bool:
        parts = path.parts
        # Ignore any path component in the ignore list
        if any(part in IGNORE_DIRS for part in parts):
            return True
        # Allow JARVIS trigger files (they start with . but we need them)
        if path.name.startswith(TRIGGER_PREFIX):
            return False
        # Ignore other hidden files
        if path.name.startswith("."):
            return True
        # Ignore temp files
        if path.suffix in (".tmp", ".part", ".swp"):
            return True
        return False


