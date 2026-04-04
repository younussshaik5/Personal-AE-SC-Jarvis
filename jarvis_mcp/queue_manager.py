"""
JARVIS Persistent Job Queue
Survives Claude Desktop restarts. Works even when Claude is closed.

When user adds files while Claude is closed:
  → Files detected via mtime comparison on next startup
  → Missing skills queued automatically
  → Queue processes immediately when Claude (re)opens

Queue stored at: ~/.jarvis/queue.json
File state at:   ~/.jarvis/file_state.json
"""

import json
import uuid
import logging
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

log = logging.getLogger(__name__)

JARVIS_DIR = Path.home() / ".jarvis"
QUEUE_FILE = JARVIS_DIR / "queue.json"
STATE_FILE = JARVIS_DIR / "file_state.json"

# Which core files trigger which skills when modified
FILE_TRIGGER_MAP = {
    "deal_stage.json":      ["account_summary", "quick_insights", "risk_report", "meddpicc"],
    "discovery.md":         ["demo_strategy", "value_architecture", "battlecard",
                             "meeting_prep", "followup_email", "technical_risk"],
    "company_research.md":  ["battlecard", "competitive_intelligence", "competitor_pricing",
                             "account_summary"],
    "CLAUDE.md":            ["account_summary", "risk_report"],
}

# All auto-generatable skills (subset of SKILL_FILES — ones that work from account context alone)
AUTO_SKILLS = [
    "account_summary", "quick_insights", "battlecard", "meddpicc",
    "risk_report", "value_architecture", "competitive_intelligence",
    "competitor_pricing", "meeting_prep", "demo_strategy",
    "followup_email", "technical_risk", "sow",
]


class QueueManager:
    """
    Persistent skill generation queue.

    Usage:
        q = QueueManager()
        q.scan_missing_skills(accounts_root, skill_files)   # queue missing outputs
        q.scan_changed_files(accounts_root)                 # queue changed files
        await q.process_all(llm, config)                    # run all pending jobs
    """

    def __init__(self):
        JARVIS_DIR.mkdir(parents=True, exist_ok=True)
        self._jobs: List[Dict] = []
        self._file_state: Dict[str, float] = {}
        self._load()

    # ── Persistence ──────────────────────────────────────────────────────────

    def _load(self):
        if QUEUE_FILE.exists():
            try:
                self._jobs = json.loads(QUEUE_FILE.read_text())
            except Exception:
                self._jobs = []
        if STATE_FILE.exists():
            try:
                self._file_state = json.loads(STATE_FILE.read_text())
            except Exception:
                self._file_state = {}

    def _save_queue(self):
        try:
            QUEUE_FILE.write_text(json.dumps(self._jobs, indent=2))
        except Exception as e:
            log.warning(f"Could not save queue: {e}")

    def _save_state(self):
        try:
            STATE_FILE.write_text(json.dumps(self._file_state, indent=2))
        except Exception as e:
            log.warning(f"Could not save state: {e}")

    # ── Job Management ────────────────────────────────────────────────────────

    def add_job(self, account: str, skill_key: str, priority: int = 5) -> str:
        """Add skill generation job. No-op if already pending. Returns job ID."""
        for j in self._jobs:
            if j["account"] == account and j["skill"] == skill_key and j["status"] == "pending":
                return j["id"]

        job = {
            "id": str(uuid.uuid4())[:8],
            "account": account,
            "skill": skill_key,
            "status": "pending",
            "priority": priority,
            "added_at": datetime.now().isoformat(),
            "processed_at": None,
            "error": None,
        }
        self._jobs.append(job)
        self._save_queue()
        log.info(f"Queued: [{skill_key}] for {account}")
        return job["id"]

    def get_pending(self) -> List[Dict]:
        """Pending jobs, sorted by priority (1=highest)."""
        return sorted(
            [j for j in self._jobs if j["status"] == "pending"],
            key=lambda j: j.get("priority", 5)
        )

    def mark_processing(self, job_id: str):
        for j in self._jobs:
            if j["id"] == job_id:
                j["status"] = "processing"
                self._save_queue()
                return

    def mark_done(self, job_id: str):
        for j in self._jobs:
            if j["id"] == job_id:
                j["status"] = "done"
                j["processed_at"] = datetime.now().isoformat()
                self._save_queue()
                return

    def mark_failed(self, job_id: str, error: str):
        for j in self._jobs:
            if j["id"] == job_id:
                j["status"] = "failed"
                j["error"] = str(error)[:300]
                j["processed_at"] = datetime.now().isoformat()
                self._save_queue()
                return

    def clear_done(self):
        """Prune completed jobs (keep last 100 for history)."""
        done = [j for j in self._jobs if j["status"] == "done"]
        other = [j for j in self._jobs if j["status"] != "done"]
        self._jobs = other + done[-100:]
        self._save_queue()

    def reset_processing(self):
        """Reset any 'processing' jobs back to 'pending' (handles crash recovery)."""
        changed = False
        for j in self._jobs:
            if j["status"] == "processing":
                j["status"] = "pending"
                changed = True
        if changed:
            self._save_queue()

    # ── Scanning ──────────────────────────────────────────────────────────────

    @staticmethod
    def _is_skeleton(filepath: Path) -> bool:
        """Return True if a skill file exists but contains only headings/separators/placeholders — no real content."""
        import re as _re
        try:
            text = filepath.read_text(encoding="utf-8").strip()
            if len(text) < 50:
                return True
            real = 0
            for line in text.splitlines():
                s = line.strip()
                if (s
                        and not s.startswith("#")
                        and not _re.match(r"^-{2,}$", s)
                        and not s.startswith("_No data generated")):
                    real += 1
                    if real >= 4:
                        return False
            return True
        except Exception:
            return False

    def scan_missing_skills(self, accounts_root: Path, skill_files: Dict) -> int:
        """Queue all missing or skeleton skill output files across all accounts. Returns count."""
        if not accounts_root.exists():
            return 0
        count = 0

        def _check(folder: Path, account: str):
            nonlocal count
            if not (folder / "deal_stage.json").exists():
                return
            for skill_key in AUTO_SKILLS:
                if skill_key not in skill_files:
                    continue
                filepath = folder / skill_files[skill_key]["file"]
                if filepath.exists() and self._is_skeleton(filepath):
                    # Delete skeleton so it is treated as missing and re-generated cleanly
                    try:
                        filepath.unlink()
                        log.info(f"Removed skeleton file {filepath.name} for {account} — will regenerate")
                    except Exception:
                        pass
                if not filepath.exists():
                    self.add_job(account, skill_key, priority=5)
                    count += 1

        for folder in sorted(accounts_root.iterdir()):
            if not folder.is_dir() or folder.name.startswith('.'):
                continue
            _check(folder, folder.name)
            for sub in sorted(folder.iterdir()):
                if not sub.is_dir() or sub.name.startswith('.'):
                    continue
                _check(sub, f"{folder.name}/{sub.name}")

        if count:
            log.info(f"Queued {count} missing skill outputs")
        return count

    def scan_changed_files(self, accounts_root: Path) -> int:
        """Detect files changed since last run and queue affected skills. Returns count."""
        if not accounts_root.exists():
            return 0
        count = 0
        new_state = {}

        def _check(folder: Path, account: str):
            nonlocal count
            for filename, triggers in FILE_TRIGGER_MAP.items():
                fpath = folder / filename
                if not fpath.exists():
                    continue
                try:
                    mtime = fpath.stat().st_mtime
                except OSError:
                    continue
                key = str(fpath)
                new_state[key] = mtime
                last = self._file_state.get(key)
                if last is not None and mtime > last:
                    log.info(f"Changed: {filename} in {account} → queuing {len(triggers)} skills")
                    for skill_key in triggers:
                        self.add_job(account, skill_key, priority=1)
                    count += 1

        for folder in sorted(accounts_root.iterdir()):
            if not folder.is_dir() or folder.name.startswith('.'):
                continue
            _check(folder, folder.name)
            for sub in sorted(folder.iterdir()):
                if not sub.is_dir() or sub.name.startswith('.'):
                    continue
                _check(sub, f"{folder.name}/{sub.name}")

        self._file_state.update(new_state)
        self._save_state()
        if count:
            log.info(f"Detected {count} changed files, queued affected skills")
        return count

    def snapshot_state(self, accounts_root: Path):
        """Record current file mtimes (call after first-run to baseline change detection)."""
        if not accounts_root.exists():
            return
        for fpath in accounts_root.rglob("*.json"):
            try:
                self._file_state[str(fpath)] = fpath.stat().st_mtime
            except OSError:
                pass
        for fpath in accounts_root.rglob("*.md"):
            try:
                self._file_state[str(fpath)] = fpath.stat().st_mtime
            except OSError:
                pass
        self._save_state()

    # ── Processing ───────────────────────────────────────────────────────────

    async def process_all(self, llm_manager, config_manager) -> int:
        """
        Process all pending jobs using jarvis_mcp skills directly.
        Returns count of successfully processed jobs.
        """
        # Reset any jobs stuck in 'processing' from a previous crash
        self.reset_processing()

        # Import skill registry
        try:
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            from jarvis_mcp.skills import SKILL_REGISTRY
        except ImportError as e:
            log.error(f"Cannot import skills for queue processing: {e}")
            return 0

        pending = self.get_pending()
        if not pending:
            return 0

        log.info(f"Processing {len(pending)} queued jobs…")
        processed = 0

        for job in pending:
            skill_key = job["skill"]
            account = job["account"]

            skill_class = SKILL_REGISTRY.get(skill_key)
            if not skill_class:
                self.mark_failed(job["id"], f"Unknown skill: {skill_key}")
                continue

            self.mark_processing(job["id"])
            try:
                skill = skill_class(llm_manager, config_manager)
                await skill.execute({"account_name": account})
                self.mark_done(job["id"])
                processed += 1
                log.info(f"✅ [{skill_key}] for {account}")
            except Exception as e:
                self.mark_failed(job["id"], str(e))
                log.error(f"❌ [{skill_key}] for {account}: {e}")

        if processed:
            self.clear_done()
            # Snapshot updated state so we don't re-queue the files we just created
            try:
                self.snapshot_state(config_manager.accounts_root)
            except Exception:
                pass

        return processed

    # ── Status ───────────────────────────────────────────────────────────────

    def get_status(self) -> Dict:
        """Return queue status for API / dashboard display."""
        pending   = [j for j in self._jobs if j["status"] == "pending"]
        proc      = [j for j in self._jobs if j["status"] == "processing"]
        done      = [j for j in self._jobs if j["status"] == "done"]
        failed    = [j for j in self._jobs if j["status"] == "failed"]

        by_account: Dict[str, List[str]] = {}
        for j in pending + proc:
            by_account.setdefault(j["account"], []).append(j["skill"])

        return {
            "pending":    len(pending),
            "processing": len(proc),
            "done":       len(done),
            "failed":     len(failed),
            "total":      len(self._jobs),
            "is_active":  len(pending) + len(proc) > 0,
            "by_account": by_account,
            "recent":     self._jobs[-20:],
        }
