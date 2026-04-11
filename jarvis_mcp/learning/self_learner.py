"""
SelfLearner — records what ran, when, and why per account.

Writes two files into every account folder:
  _skill_timeline.json   machine-readable: {skill: {last_run, trigger, status}}
  _evolution_log.md      human-readable append log — read by ALL skills as context

When a skill runs, it reads _evolution_log.md via build_context_block.
So every subsequent skill knows what changed and when — making each run
smarter than the last.

Example _evolution_log.md entry:
  [2026-04-02 10:30] meddpicc regenerated (file:discovery.md) — AMBER overall, RED on EB
  [2026-04-02 10:31] risk_report cascade from meddpicc — 2 HIGH risks identified
  [2026-04-02 10:32] value_architecture cascade from meddpicc — ROI model updated
"""

import json
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

log = logging.getLogger(__name__)

TIMELINE_FILE  = "_skill_timeline.json"
EVOLUTION_FILE = "_evolution_log.md"
MAX_LOG_LINES  = 200  # keep rolling window to avoid unbounded growth


class SelfLearner:
    """
    Lightweight per-account skill evolution tracker.
    Thread-safe via asyncio lock per account.
    """

    def __init__(self, accounts_root: Path):
        self.accounts_root = accounts_root
        self._locks: Dict[str, asyncio.Lock] = {}

    def _lock_for(self, account_name: str) -> asyncio.Lock:
        if account_name not in self._locks:
            self._locks[account_name] = asyncio.Lock()
        return self._locks[account_name]

    def _account_path(self, account_name: str) -> Optional[Path]:
        """Find account directory — supports flat and parent/child structures."""
        direct = self.accounts_root / account_name
        if direct.exists():
            return direct
        # Search one level deep (parent/child)
        for parent in self.accounts_root.iterdir():
            if parent.is_dir():
                child = parent / account_name
                if child.exists():
                    return child
        return None

    async def record(
        self,
        account_name: str,
        skill_name: str,
        trigger: str,
        status: str = "ok",
        summary: str = "",
    ) -> None:
        """
        Record a skill run. Updates timeline JSON and appends to evolution log.
        Called after every skill completes (user-triggered or queue-cascaded).
        """
        path = self._account_path(account_name)
        if not path:
            return

        async with self._lock_for(account_name):
            await self._update_timeline(path, skill_name, trigger, status)
            await self._append_evolution_log(path, skill_name, trigger, status, summary)

    async def _update_timeline(
        self, path: Path, skill_name: str, trigger: str, status: str
    ) -> None:
        timeline_path = path / TIMELINE_FILE
        try:
            if timeline_path.exists():
                with open(timeline_path) as f:
                    timeline = json.load(f)
            else:
                timeline = {}

            timeline[skill_name] = {
                "last_run": datetime.now(timezone.utc).isoformat(),
                "trigger": trigger,
                "status": status,
            }

            with open(timeline_path, "w") as f:
                json.dump(timeline, f, indent=2)
        except Exception as e:
            log.warning(f"[learner] timeline write failed ({account_name}/{skill_name}): {e}")

    async def _append_evolution_log(
        self, path: Path, skill_name: str, trigger: str, status: str, summary: str
    ) -> None:
        log_path = path / EVOLUTION_FILE
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Status icon
        icon = "✓" if status == "ok" else "✗"
        line = f"[{now}] {icon} {skill_name} (trigger: {trigger})"
        if summary:
            line += f" — {summary}"
        line += "\n"

        try:
            # Read existing lines
            existing = []
            if log_path.exists():
                with open(log_path) as f:
                    existing = f.readlines()

            # Prepend header if new file
            if not existing:
                existing = ["# JARVIS Evolution Log\n",
                            "# Auto-generated — do not edit manually\n",
                            "# Each entry = one skill run and what triggered it\n\n"]

            # Append new line, then trim to MAX_LOG_LINES content lines
            existing.append(line)
            header = [l for l in existing if l.startswith("#")]
            content = [l for l in existing if not l.startswith("#")]
            if len(content) > MAX_LOG_LINES:
                content = content[-MAX_LOG_LINES:]

            with open(log_path, "w") as f:
                f.writelines(header + ["\n"] + content)

        except Exception as e:
            log.warning(f"[learner] evolution log write failed ({path.name}): {e}")

    def get_timeline(self, account_name: str) -> Dict[str, Any]:
        """Return current skill timeline for an account (sync, for status queries)."""
        path = self._account_path(account_name)
        if not path:
            return {}
        timeline_path = path / TIMELINE_FILE
        if not timeline_path.exists():
            return {}
        try:
            with open(timeline_path) as f:
                return json.load(f)
        except Exception:
            return {}

    def stale_skills(self, account_name: str, max_age_hours: float = 24.0) -> list:
        """
        Return skills whose last run is older than max_age_hours.
        Useful for surfacing 'these skills need refreshing' in account summary.
        """
        timeline = self.get_timeline(account_name)
        now = datetime.now(timezone.utc)
        stale = []
        for skill, meta in timeline.items():
            try:
                last = datetime.fromisoformat(meta["last_run"])
                age_hours = (now - last).total_seconds() / 3600
                if age_hours > max_age_hours:
                    stale.append({"skill": skill, "age_hours": round(age_hours, 1), "trigger": meta.get("trigger")})
            except Exception:
                continue
        return sorted(stale, key=lambda x: x["age_hours"], reverse=True)
