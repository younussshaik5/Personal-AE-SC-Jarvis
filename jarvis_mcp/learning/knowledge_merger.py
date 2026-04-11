"""
KnowledgeMerger — appends new intel into discovery.md without overwriting anything.

Strategy:
  - Never delete or overwrite existing content
  - Append a timestamped section at the bottom: "## [YYYY-MM-DD HH:MM] Intel from {source}"
  - Each section is self-contained and traceable
  - JARVIS reads the full file, so all appended intel is picked up on next skill run

Why append-only?
  - Safe: no data loss even if extraction produces noise
  - Traceable: every addition has a timestamp and source
  - Additive: the file grows richer over time — that's the intent
  - LLMs handle long files fine; the context block truncates gracefully

Also updates deal_stage.json if hard deal facts are found
(stage, ARR, stakeholder names, timeline) — but conservatively.
"""

import json
import re
import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

log = logging.getLogger(__name__)

# Skills whose outputs should feed back into discovery.md
# (outputs that often contain new deal facts)
FEEDBACK_SKILLS = {
    "meddpicc",
    "risk_report",
    "conversation_extractor",
    "meeting_summary",
    "technical_risk",
    "value_architecture",
    "competitive_intelligence",
}

# Skills whose outputs should NOT feed back (they read discovery, not add to it)
NO_FEEDBACK_SKILLS = {
    "proposal",
    "sow",
    "followup_email",
    "meeting_prep",
    "demo_strategy",
    "battlecard",
    "discovery",
    "account_summary",
    "quick_insights",
    "documentation",
    "html_generator",
    "custom_template",
    "architecture_diagram",
}


class KnowledgeMerger:
    """
    Merges extracted intel into account knowledge files.
    Thread-safe via per-account asyncio locks.

    Cycle guard: tracks when WE last wrote to discovery.md per account.
    FileWatcher checks this to skip changes we caused — preventing infinite loops.
    """

    def __init__(self, accounts_root: Path):
        self.accounts_root = accounts_root
        self._locks: Dict[str, asyncio.Lock] = {}
        # Cycle guard: "account_name" → timestamp of our last write
        self._self_writes: Dict[str, float] = {}
        self.SELF_WRITE_COOLDOWN = 1800.0  # 30 min cooldown — full cascade takes 20-40 min

    def was_self_written(self, account_name: str) -> bool:
        """Returns True if we wrote to this account's discovery.md within the cooldown window."""
        last = self._self_writes.get(account_name, 0)
        return (time.monotonic() - last) < self.SELF_WRITE_COOLDOWN

    def _lock_for(self, account_name: str) -> asyncio.Lock:
        if account_name not in self._locks:
            self._locks[account_name] = asyncio.Lock()
        return self._locks[account_name]

    @staticmethod
    def _safe_name(account_name: str) -> str:
        return account_name.replace(" ", "_").replace("/", "_")

    def _account_path(self, account_name: str) -> Optional[Path]:
        # Always try sanitized name first (canonical form)
        safe = self._safe_name(account_name)
        direct = self.accounts_root / safe
        if direct.exists():
            return direct
        # Fallback: raw name (legacy folders created before sanitization fix)
        raw = self.accounts_root / account_name
        if raw.exists():
            return raw
        return None

    async def merge(
        self,
        account_name: str,
        intel: str,
        source: str,
    ) -> bool:
        """
        Append intel to discovery.md with a timestamped header.
        Returns True if something was written, False if skipped.
        """
        if not intel or not intel.strip():
            return False

        path = self._account_path(account_name)
        if not path:
            log.warning(f"[merger] Account not found: {account_name}")
            return False

        async with self._lock_for(account_name):
            return await self._append_to_discovery(path, intel, source, account_name)

    async def _append_to_discovery(
        self, path: Path, intel: str, source: str, account_name: str
    ) -> bool:
        discovery_path = path / "discovery.md"
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Build the new section
        section = (
            f"\n\n---\n\n"
            f"## [{now}] Intel from: {source}\n\n"
            f"{intel.strip()}\n"
        )

        try:
            # Read existing content
            existing = ""
            if discovery_path.exists():
                with open(discovery_path) as f:
                    existing = f.read()

            # Check for near-duplicate (same source + same day already appended)
            day = datetime.now().strftime("%Y-%m-%d")
            duplicate_marker = f"## [{day}"
            if duplicate_marker in existing and source in existing:
                # Same source wrote today — still append, different time
                pass

            with open(discovery_path, "a") as f:
                f.write(section)

            # Record self-write AFTER successful write — keyed by account_name
            # so was_self_written() lookup matches correctly
            self._self_writes[account_name] = time.monotonic()

            log.info(f"[merger] Appended intel to {account_name}/discovery.md (from {source})")

            # Sync any extracted stakeholders to deal_stage.json
            self._sync_stakeholders_to_deal_stage(path, intel, account_name)

            return True

        except Exception as e:
            log.error(f"[merger] Write failed for {account_name}: {e}")
            return False

    # ── Stakeholder + deal fact sync ──────────────────────────────────────────

    @staticmethod
    def _parse_stakeholders_from_intel(intel: str) -> List[Dict]:
        """
        Parse structured stakeholders from an ### New Stakeholders section.
        Handles formats:
          - **Name** – title/company, role (notes)
          - **Name**: description
          - - Name, title
        """
        stakeholders = []
        in_section = False
        for line in intel.splitlines():
            stripped = line.strip()
            if re.match(r"^###?\s+New Stakeholders", stripped, re.IGNORECASE):
                in_section = True
                continue
            if in_section:
                if stripped.startswith("##"):
                    break  # next section
                if not stripped or stripped.startswith("#"):
                    continue
                # Strip leading bullet
                content = re.sub(r"^[-*]\s+", "", stripped)
                # Extract bold name: **Name**
                m = re.match(r"\*\*(.+?)\*\*\s*[–\-:]\s*(.*)", content)
                if m:
                    name = m.group(1).strip()
                    rest = m.group(2).strip()
                    # Split rest into title and notes at first comma or dash
                    parts = re.split(r",\s*", rest, 1)
                    title = parts[0].strip() if parts else ""
                    notes = parts[1].strip() if len(parts) > 1 else ""
                    # Extract role signals
                    combined = (rest + " " + notes).lower()
                    if "economic buyer" in combined or "budget" in combined:
                        role = "Economic Buyer"
                    elif "champion" in combined or "advocate" in combined:
                        role = "Champion"
                    elif "blocker" in combined or "detractor" in combined:
                        role = "Blocker"
                    elif "technical" in combined or "it " in combined:
                        role = "Technical Evaluator"
                    else:
                        role = "Stakeholder"
                    stakeholders.append({
                        "name": name,
                        "title": title,
                        "role": role,
                        "notes": rest[:200],
                    })
                elif content:
                    # Plain bullet — use as name/notes
                    parts = content.split(",", 1)
                    stakeholders.append({
                        "name": parts[0].strip(),
                        "title": parts[1].strip() if len(parts) > 1 else "",
                        "role": "Stakeholder",
                        "notes": content[:200],
                    })
        return stakeholders

    def _sync_stakeholders_to_deal_stage(
        self, account_path: Path, intel: str, account_name: str
    ) -> None:
        """
        Parse stakeholders from intel and merge (dedupe by name) into deal_stage.json.
        Runs synchronously — called from inside the async lock context.
        """
        new_stakeholders = self._parse_stakeholders_from_intel(intel)
        if not new_stakeholders:
            return

        deal_stage_path = account_path / "deal_stage.json"
        try:
            if deal_stage_path.exists():
                with open(deal_stage_path, "r", encoding="utf-8") as f:
                    deal = json.load(f)
            else:
                deal = {}
        except Exception as e:
            log.warning(f"[merger] Could not read deal_stage.json for {account_name}: {e}")
            return

        existing = deal.setdefault("stakeholders", [])
        existing_names = {
            (s.get("name") or "").strip().lower()
            for s in existing
            if isinstance(s, dict)
        }

        added = 0
        for s in new_stakeholders:
            if s["name"].lower() not in existing_names:
                existing.append(s)
                existing_names.add(s["name"].lower())
                added += 1

        if added:
            deal["stakeholders"] = existing
            try:
                with open(deal_stage_path, "w", encoding="utf-8") as f:
                    json.dump(deal, f, indent=2)
                log.info(
                    f"[merger] Synced {added} new stakeholder(s) to "
                    f"{account_name}/deal_stage.json"
                )
            except Exception as e:
                log.error(f"[merger] Failed to write deal_stage.json for {account_name}: {e}")

    async def merge_from_skill_output(
        self,
        account_name: str,
        skill_name: str,
        output: str,
        extractor,
    ) -> bool:
        """
        Extract intel from a skill's output and merge it back.
        Only runs for skills in FEEDBACK_SKILLS — others are skipped.
        """
        if skill_name in NO_FEEDBACK_SKILLS:
            return False
        if skill_name not in FEEDBACK_SKILLS:
            return False
        if not output or output.strip().startswith("❌"):
            return False

        intel = await extractor.extract(
            text=output,
            source=f"skill:{skill_name}",
            max_chars=6000,
        )
        if not intel:
            return False

        return await self.merge(account_name, intel, source=f"skill:{skill_name}")

    async def merge_from_file(
        self,
        account_name: str,
        file_path: Path,
        extractor,
    ) -> bool:
        """
        Read a file, extract intel, merge into discovery.md.
        Called by the file watcher for any new/modified non-source file.
        """
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception as e:
            log.warning(f"[merger] Could not read {file_path}: {e}")
            return False

        if not text.strip():
            return False

        intel = await extractor.extract(
            text=text,
            source=f"file:{file_path.name}",
            max_chars=8000,
        )
        if not intel:
            return False

        return await self.merge(account_name, intel, source=f"file:{file_path.name}")
