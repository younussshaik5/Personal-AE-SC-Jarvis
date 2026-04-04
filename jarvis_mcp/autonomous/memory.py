"""
Persistent memory store for JARVIS autonomous agent.
Tracks attempt history, quality scores, todos, and global insights.
Stored at ~/.jarvis/autonomous_memory.json — survives server restarts.
"""

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

log = logging.getLogger(__name__)

_MEMORY_PATH = Path.home() / ".jarvis" / "autonomous_memory.json"
_MAX_INSIGHTS = 100


class AutonomousMemory:
    """
    Persistent memory for autonomous retry tracking.

    Schema:
      {
        "skills": {
          "<account>::<skill>": {
            "attempts": int,
            "outcomes": [...],
            "strategies_tried": [...],
            "quality_scores": [...],
            "last_error": str,
            "last_attempt_at": float,
            "last_success_at": float | null
          }
        },
        "todos": [
          {
            "id": str,
            "account": str,
            "skill": str,
            "reason": str,
            "strategies_tried": [...],
            "created_at": float,
            "resolved": bool,
            "resolved_at": float | null
          }
        ],
        "insights": [str]
      }
    """

    def __init__(self):
        _MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        if _MEMORY_PATH.exists():
            try:
                with open(_MEMORY_PATH, "r") as f:
                    self._data = json.load(f)
            except Exception as e:
                log.warning(f"[memory] Failed to load {_MEMORY_PATH}: {e} — starting fresh")
                self._data = {}
        else:
            self._data = {}

        # Ensure top-level keys exist
        self._data.setdefault("skills", {})
        self._data.setdefault("todos", [])
        self._data.setdefault("insights", [])

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _key(self, account: str, skill: str) -> str:
        return f"{account}::{skill}"

    def _save(self) -> None:
        try:
            with open(_MEMORY_PATH, "w") as f:
                json.dump(self._data, f, indent=2)
        except Exception as e:
            log.error(f"[memory] Failed to save: {e}")

    # ── Skill attempt tracking ────────────────────────────────────────────────

    def record_attempt(
        self,
        account: str,
        skill: str,
        outcome: str,
        strategy: str,
        quality: int = 0,
        error: str = "",
    ) -> None:
        """
        Record a single attempt for account+skill.

        outcome: success | skeleton | reasoning_dump | error | partial
        """
        key = self._key(account, skill)
        entry = self._data["skills"].setdefault(key, {
            "attempts": 0,
            "outcomes": [],
            "strategies_tried": [],
            "quality_scores": [],
            "last_error": "",
            "last_attempt_at": None,
            "last_success_at": None,
        })

        entry["attempts"] += 1
        entry["outcomes"].append(outcome)
        entry["strategies_tried"].append(strategy)
        entry["quality_scores"].append(quality)
        entry["last_error"] = error
        entry["last_attempt_at"] = time.time()

        if outcome in ("success", "partial"):
            entry["last_success_at"] = time.time()

        self._save()

    def get_history(self, account: str, skill: str) -> Dict[str, Any]:
        """Return full attempt history dict for account+skill."""
        key = self._key(account, skill)
        return self._data["skills"].get(key, {
            "attempts": 0,
            "outcomes": [],
            "strategies_tried": [],
            "quality_scores": [],
            "last_error": "",
            "last_attempt_at": None,
            "last_success_at": None,
        })

    def strategies_tried(self, account: str, skill: str) -> List[str]:
        """Return list of strategies already tried for account+skill."""
        return self.get_history(account, skill).get("strategies_tried", [])

    # ── Todo management ───────────────────────────────────────────────────────

    def add_todo(
        self,
        account: str,
        skill: str,
        reason: str,
        strategies_tried: List[str],
    ) -> str:
        """
        Add or update a todo for account+skill.
        If an unresolved todo already exists for this account+skill, update it in place.
        Returns todo_id.
        """
        # Check for existing unresolved todo
        for todo in self._data["todos"]:
            if todo["account"] == account and todo["skill"] == skill and not todo["resolved"]:
                todo["reason"] = reason
                todo["strategies_tried"] = strategies_tried
                todo["created_at"] = time.time()
                self._save()
                return todo["id"]

        todo_id = str(uuid.uuid4())[:8]
        self._data["todos"].append({
            "id": todo_id,
            "account": account,
            "skill": skill,
            "reason": reason,
            "strategies_tried": strategies_tried,
            "created_at": time.time(),
            "resolved": False,
            "resolved_at": None,
        })
        self._save()
        return todo_id

    def resolve_todo(self, account: str, skill: str) -> None:
        """Mark any unresolved todo for account+skill as resolved."""
        for todo in self._data["todos"]:
            if todo["account"] == account and todo["skill"] == skill and not todo["resolved"]:
                todo["resolved"] = True
                todo["resolved_at"] = time.time()
        self._save()

    def get_todos(self, resolved: bool = False) -> List[Dict[str, Any]]:
        """Return todos filtered by resolved status."""
        return [t for t in self._data["todos"] if t["resolved"] == resolved]

    # ── Global insights ───────────────────────────────────────────────────────

    def add_insight(self, insight_str: str) -> None:
        """Add a deduplicated insight. Caps at _MAX_INSIGHTS."""
        if insight_str in self._data["insights"]:
            return
        self._data["insights"].append(insight_str)
        if len(self._data["insights"]) > _MAX_INSIGHTS:
            self._data["insights"] = self._data["insights"][-_MAX_INSIGHTS:]
        self._save()

    def get_insights(self) -> List[str]:
        """Return all global insights."""
        return list(self._data["insights"])

    # ── Summary ───────────────────────────────────────────────────────────────

    def summary(self) -> Dict[str, Any]:
        """High-level stats dict."""
        skills = self._data["skills"]
        successful = sum(
            1 for v in skills.values()
            if any(o in ("success", "partial") for o in v.get("outcomes", []))
        )
        pending_todos = len(self.get_todos(resolved=False))
        return {
            "skills_tracked": len(skills),
            "skills_successful": successful,
            "pending_todos": pending_todos,
            "global_insights": len(self._data["insights"]),
        }
