"""
File watcher — monitors ACCOUNTS/ for changes and queues relevant skills.

Two types of events:

1. SOURCE FILE changed (discovery.md, company_research.md, deal_stage.json)
   → Queue skills directly via FILE_TRIGGERS (existing behaviour)

2. ANY OTHER FILE added/modified (.md, .txt, .csv, .json excluding deal_stage)
   → Pipe through IntelligenceExtractor → KnowledgeMerger → appends to discovery.md
   → discovery.md change triggers the cascade automatically

This means: drop ANY file into an account folder → JARVIS reads it,
extracts intel, updates discovery.md, and regenerates all outputs.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, Optional, Set

from .skill_queue import SkillQueue, PRIORITY_HIGH
from .dependency_graph import FILE_TRIGGERS, SKIP_AUTO_QUEUE

log = logging.getLogger(__name__)

DEBOUNCE = 2.0  # seconds

# File extensions JARVIS will try to extract intel from
INGESTIBLE_EXTENSIONS = {".md", ".txt", ".text", ".csv", ".log"}

# Filenames that are JARVIS-generated outputs — don't feed back into themselves
JARVIS_OUTPUT_FILES = {
    "battlecard.md", "meddpicc.md", "risk_report.md", "proposal.md",
    "sow.md", "value_architecture.md", "demo_strategy.md", "meeting_prep.md",
    "account_summary.md", "competitive_intelligence.md", "competitor_pricing.md",
    "technical_risk.md", "discovery.md", "quick_insights.md", "followup_email.md",
    "architecture_diagram.md", "knowledge_builder.md", "documentation.md",
    "_evolution_log.md", "_skill_timeline.json", "deal_stage.json",
    "company_research.md",  # source file — handled by FILE_TRIGGERS directly
}


class FileWatcher:
    """
    Watches ACCOUNTS/ for:
      - Source file changes → queue skills (FILE_TRIGGERS)
      - New/modified ingestible files → extract intel → merge to discovery.md
    """

    def __init__(
        self,
        queue: SkillQueue,
        accounts_root: Path,
        extractor=None,     # IntelligenceExtractor — set after init
        merger=None,        # KnowledgeMerger — set after init
    ):
        self.queue = queue
        self.accounts_root = accounts_root
        self.extractor = extractor
        self.merger = merger

        self._last_trigger: Dict[str, float] = {}
        self._seen_files: Set[str] = set()       # tracks already-ingested files
        self._running = False
        self._observer = None
        self._task: asyncio.Task = None
        self._loop: asyncio.AbstractEventLoop = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._loop = asyncio.get_event_loop()

        # Snapshot existing files so we don't re-ingest on startup
        self._snapshot_existing()

        try:
            self._start_watchdog()
            log.info(f"[watcher] watchdog active on {self.accounts_root}")
        except ImportError:
            log.warning("[watcher] watchdog not available — using polling fallback")
            self._task = asyncio.ensure_future(self._poll())

    def stop(self) -> None:
        self._running = False
        if self._observer:
            self._observer.stop()
            self._observer.join()
        if self._task:
            self._task.cancel()

    def _snapshot_existing(self) -> None:
        """Mark all currently existing files as already seen — don't re-ingest on boot."""
        if not self.accounts_root.exists():
            return
        for acct in self.accounts_root.iterdir():
            if not acct.is_dir():
                continue
            scan_dirs = [acct] + [d for d in acct.iterdir() if d.is_dir()]
            for d in scan_dirs:
                for f in d.iterdir():
                    if f.is_file():
                        self._seen_files.add(str(f))

    # ── Watchdog path ─────────────────────────────────────────────────────────

    def _start_watchdog(self) -> None:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        watcher = self

        class Handler(FileSystemEventHandler):
            def on_modified(self, event):
                if not event.is_directory:
                    watcher._on_file_event(Path(event.src_path), is_new=False)

            def on_created(self, event):
                if not event.is_directory:
                    watcher._on_file_event(Path(event.src_path), is_new=True)

        self._observer = Observer()
        self._observer.schedule(Handler(), str(self.accounts_root), recursive=True)
        self._observer.start()

    def _on_file_event(self, path: Path, is_new: bool) -> None:
        """Called by watchdog thread — bridge to asyncio loop."""
        key = f"{path.parent.name}::{path.name}"
        now = time.time()
        if now - self._last_trigger.get(key, 0) < DEBOUNCE:
            return
        self._last_trigger[key] = now

        asyncio.run_coroutine_threadsafe(
            self._handle_file(path, is_new),
            self._loop,
        )

    # ── Polling fallback ──────────────────────────────────────────────────────

    async def _poll(self) -> None:
        mtimes: Dict[str, float] = {}
        while self._running:
            try:
                if self.accounts_root.exists():
                    for acct in self.accounts_root.iterdir():
                        if not acct.is_dir():
                            continue
                        scan_dirs = [acct] + [d for d in acct.iterdir() if d.is_dir()]
                        for d in scan_dirs:
                            for fp in d.iterdir():
                                if not fp.is_file():
                                    continue
                                key = f"{d.name}::{fp.name}"
                                try:
                                    mtime = fp.stat().st_mtime
                                except OSError:
                                    continue
                                is_new = key not in mtimes
                                if mtime > mtimes.get(key, 0):
                                    mtimes[key] = mtime
                                    now = time.time()
                                    if now - self._last_trigger.get(key, 0) >= DEBOUNCE:
                                        self._last_trigger[key] = now
                                        await self._handle_file(fp, is_new)
            except Exception as e:
                log.error(f"[watcher/poll] {e}")
            await asyncio.sleep(3.0)

    # ── Unified file handler ──────────────────────────────────────────────────

    async def _handle_file(self, path: Path, is_new: bool) -> None:
        filename = path.name
        account_name = path.parent.name

        # 1. Source file changed → queue skills directly
        if filename in FILE_TRIGGERS:
            log.info(f"[watcher] Source changed: {account_name}/{filename}")
            await self._enqueue_triggers(account_name, filename)
            return

        # 2. New ingestible file dropped → extract intel → merge to discovery.md
        if (
            path.suffix in INGESTIBLE_EXTENSIONS
            and filename not in JARVIS_OUTPUT_FILES
            and str(path) not in self._seen_files
            and self.extractor
            and self.merger
        ):
            self._seen_files.add(str(path))
            log.info(f"[watcher] New file detected: {account_name}/{filename} — ingesting")
            asyncio.ensure_future(self._ingest_file(account_name, path))

    async def _ingest_file(self, account_name: str, path: Path) -> None:
        """Extract intel from a new file and merge into discovery.md."""
        try:
            merged = await self.merger.merge_from_file(account_name, path, self.extractor)
            if merged:
                log.info(f"[watcher] Intel merged from {path.name} into {account_name}/discovery.md")
                # discovery.md was updated — file watcher will detect and cascade
        except Exception as e:
            log.error(f"[watcher] Ingest failed for {path}: {e}")

    async def _enqueue_triggers(self, account_name: str, filename: str) -> None:
        for skill_name in FILE_TRIGGERS.get(filename, []):
            if skill_name in SKIP_AUTO_QUEUE:
                continue
            await self.queue.put(
                account_name=account_name,
                skill_name=skill_name,
                priority=PRIORITY_HIGH,
                trigger=f"file:{filename}",
            )
