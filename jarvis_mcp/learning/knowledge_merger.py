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
import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

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
        self.SELF_WRITE_COOLDOWN = 300.0  # 5 min cooldown — skills take 3-5 min to run

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
            return True

        except Exception as e:
            log.error(f"[merger] Write failed for {account_name}: {e}")
            return False

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
