#!/usr/bin/env python3
"""
Summary Refresh Skill — auto-update account summary.md with latest intel.

Triggers: document.processed, conversation.message, meeting.summary.ready, file.modified on INTEL files.
Action: Regenerates ACCOUNTS/{account}/summary.md with current state.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event
from jarvis.utils.config import ConfigManager


class SummaryRefreshSkill:
    """Automatically refresh account summary.md when intel updates."""

    def __init__(self, config: ConfigManager, event_bus: EventBus):
        self.config = config
        self.event_bus = event_bus
        self.logger = JARVISLogger("summary_refresh")
        self._workspace_root = Path(self.config.workspace_root).resolve()
        self._accounts_dir = self._workspace_root / "ACCOUNTS"
        self._refresh_tasks: Dict[str, asyncio.Task] = {}
        self._refresh_tasks: Dict[str, asyncio.Task] = {}

    async def start(self):
        """Start the skill."""
        # Subscribe to all events that indicate new intel
        self.event_bus.subscribe("document.processed", self._on_intel_updated)
        self.event_bus.subscribe("conversation.message", self._on_conversation)
        self.event_bus.subscribe("meeting.summary.ready", self._on_meeting)
        self.event_bus.subscribe("file.modified", self._on_file_modified)
        self.logger.info("SummaryRefreshSkill started")

    async def stop(self):
        """Stop the skill."""
        self.logger.info("SummaryRefreshSkill stopped")

    async def _on_intel_updated(self, event: Event):
        """Handle any intel update event."""
        account_name = event.data.get("account")
        if account_name:
            await self._debounced_refresh(account_name)

    async def _on_conversation(self, event: Event):
        """Handle conversation message - determine account from workspace."""
        workspace_dir = event.data.get("workspace_dir", "")
        if workspace_dir:
            account_name = self._extract_account_name(Path(workspace_dir))
            if account_name:
                await self._debounced_refresh(account_name)

    async def _on_meeting(self, event: Event):
        """Handle meeting summary ready."""
        account_name = event.data.get("account")
        if account_name:
            await self._debounced_refresh(account_name)

    async def _on_file_modified(self, event: Event):
        """Handle file modification - only interested in INTEL files."""
        file_path = Path(event.data.get("path", ""))
        # Check if file is under an account's INTEL directory
        try:
            rel = file_path.resolve().relative_to(self._accounts_dir.resolve())
            if len(rel.parts) >= 3 and rel.parts[1] == "INTEL":
                account_name = rel.parts[0]
                await self._debounced_refresh(account_name)
        except ValueError:
            pass

    async def _debounced_refresh(self, account_name: str, delay: float = 10.0):
        """Debounce rapid refreshes using a short delay."""
        # Cancel any pending refresh for this account
        if account_name in self._refresh_tasks:
            self._refresh_tasks[account_name].cancel()
        # Schedule a new refresh after delay
        self._refresh_tasks[account_name] = asyncio.create_task(self._refresh_after_delay(account_name, delay))

    async def _refresh_after_delay(self, account_name: str, delay: float):
        try:
            await asyncio.sleep(delay)
            await self._refresh_summary(account_name)
        except asyncio.CancelledError:
            # Task was cancelled by a newer request; ignore
            pass
        finally:
            self._refresh_tasks.pop(account_name, None)

    def _extract_account_name(self, workspace_path: Path) -> Optional[str]:
        """Extract account name from a workspace path under ACCOUNTS/."""
        try:
            rel = workspace_path.resolve().relative_to(self._accounts_dir.resolve())
            candidate = rel.parts[0]
            if (self._accounts_dir / candidate).is_dir():
                return candidate
        except ValueError:
            pass
        # Fallback: scan
        for acct_dir in self._accounts_dir.iterdir():
            if acct_dir.is_dir():
                try:
                    workspace_path.resolve().relative_to(acct_dir.resolve())
                    return acct_dir.name
                except ValueError:
                    continue
        return None

    async def _refresh_summary(self, account_name: str):
        """Regenerate summary.md for the account."""
        account_dir = self._accounts_dir / account_name
        summary_file = account_dir / "summary.md"
        intel_dir = account_dir / "INTEL"

        # Gather intel sources
        summary_parts = []
        
        # 1. Deal stage
        stage_file = account_dir / "deal_stage.json"
        stage_data = {}
        if stage_file.exists():
            try:
                import json
                with open(stage_file) as f:
                    stage_data = json.load(f)
                summary_parts.append(f"## Deal Stage\n{stage_data.get('stage', 'unknown')}\n")
            except Exception:
                pass

        # 2. Recent activities (last 10)
        activities_file = account_dir / "activities.jsonl"
        if activities_file.exists():
            try:
                import json
                with open(activities_file) as f:
                    lines = f.readlines()[-10:]
                if lines:
                    summary_parts.append("## Recent Activities\n")
                    for line in lines[-5:]:
                        act = json.loads(line)
                        summary_parts.append(f"- {act.get('timestamp')}: {act.get('summary', '')[:100]}")
            except Exception:
                pass

        # 3. Contacts
        contacts_file = intel_dir / "contacts.json"
        if contacts_file.exists():
            try:
                import json
                with open(contacts_file) as f:
                    contacts = json.load(f)
                summary_parts.append("## Key Contacts\n")
                for c in contacts.get("contacts", [])[:5]:
                    summary_parts.append(f"- {c.get('name')} ({c.get('role')}) - {c.get('email')}")
            except Exception:
                pass

        # 4. MEDDPICC
        meddpicc_file = account_dir / "MEDDPICC" / "meddpicc.json"
        if meddpicc_file.exists():
            try:
                import json
                with open(meddpicc_file) as f:
                    med = json.load(f)
                summary_parts.append("## MEDDPICC\n")
                summary_parts.append(f"- Metrics: {med.get('metrics', 'N/A')}\n")
                summary_parts.append(f"- Economic buyer: {med.get('economic_buyer', 'N/A')}\n")
                summary_parts.append(f"- Decision criteria: {med.get('decision_criteria', 'N/A')[:100]}\n")
            except Exception:
                pass

        # 5. Competitors
        battlecard_file = account_dir / "BATTLECARD" / "battlecard.md"
        if battlecard_file.exists():
            try:
                content = battlecard_file.read_text()[:500]
                summary_parts.append("## Competitors\n" + content)
            except Exception:
                pass

        # 6. Conversation snippets (last 3)
        conv_log = intel_dir / "conversation_log.md"
        if conv_log.exists():
            try:
                lines = conv_log.read_text().split('---\n')
                if len(lines) > 1:
                    summary_parts.append("## Latest Conversations\n")
                    for snippet in lines[-3:]:
                        if snippet.strip():
                            summary_parts.append(snippet[:200] + "...")
            except Exception:
                pass

        # Generate final summary
        if summary_parts:
            summary_content = "\n\n---\n\n".join(summary_parts)
        else:
            summary_content = "No intel available yet."

        # Write summary.md
        try:
            summary_file.write_text(summary_content)
            self.logger.debug("Updated summary.md", account=account_name)
        except Exception as e:
            self.logger.error("Failed to write summary", account=account_name, error=str(e))
