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
from .dependency_graph import FILE_TRIGGERS, SKIP_AUTO_QUEUE, SKILL_OUTPUT_FILES

log = logging.getLogger(__name__)

DEBOUNCE = 2.0  # seconds

# File extensions JARVIS will try to extract intel from
INGESTIBLE_EXTENSIONS = {".md", ".txt", ".text", ".csv", ".log"}

# Filenames that are JARVIS-generated outputs — don't feed back into themselves
JARVIS_OUTPUT_FILES = {
    # Skill output files — never re-ingest these as external intel
    "intelligence_brief.md",
    "battlecard.md", "meddpicc.md", "risk_report.md", "proposal.md",
    "sow.md", "value_architecture.md", "demo_strategy.md", "meeting_prep.md",
    "account_summary.md", "competitive_intelligence.md", "competitor_pricing.md",
    "technical_risk.md", "quick_insights.md", "followup_email.md",
    "architecture_diagram.md", "knowledge_builder.md", "documentation.md",
    "discovery_questions.md", "conversation_extractor.md", "conversation_summary.md",
    "meeting_summary.md", "report.html", "html_report.md", "custom_template.md",
    "deal_stage_tracker.md", "conversation_summarizer.md",
    # Internal JARVIS files
    "_evolution_log.md", "_skill_timeline.json", "deal_stage.json",
    # Account config files — never extract intel from these
    "CLAUDE.md",
    # Source files — handled by FILE_TRIGGERS directly, not via extractor
    "discovery.md", "company_research.md",
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
        self._seen_files: Set[str] = set()         # tracks already-ingested files
        self._trigger_history: Dict[str, list] = {}  # loop detection per (account::file)
        self._ingest_cooldown: Dict[str, float] = {}  # path → last ingest time
        self._running = False
        self._observer = None
        self._task: asyncio.Task = None
        self._loop: asyncio.AbstractEventLoop = None

        self.LOOP_WINDOW = 300       # seconds — rolling window for loop detection
        self.LOOP_MAX_TRIGGERS = 3   # max allowed triggers per account/file in window
        self.INGEST_COOLDOWN = 300   # seconds — don't re-ingest same file within 5 min

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._loop = asyncio.get_event_loop()

        # Snapshot existing files so we don't re-ingest on startup
        self._snapshot_existing()

        # Queue skills for accounts that already have data (handles JARVIS restarts)
        asyncio.ensure_future(self._startup_scan())

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
            self._observer.join(timeout=5)  # don't hang forever waiting for watchdog thread
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

    async def _startup_scan(self) -> None:
        """
        On startup, queue skills that are MISSING or skeleton for each account.
        Skips skills whose output already exists with real content (>= 200 bytes).
        This prevents re-generating everything on every JARVIS restart.
        """
        if not self.accounts_root.exists():
            return
        await asyncio.sleep(2.0)  # Let queue worker fully start first

        for acct in self.accounts_root.iterdir():
            if not acct.is_dir():
                continue
            account_name = acct.name
            queued = 0
            skills_seen: set = set()

            for filename, trigger_skills in FILE_TRIGGERS.items():
                if not (acct / filename).exists():
                    continue
                for skill_name in trigger_skills:
                    if skill_name in SKIP_AUTO_QUEUE or skill_name in skills_seen:
                        continue
                    skills_seen.add(skill_name)
                    output_file = SKILL_OUTPUT_FILES.get(skill_name)
                    if output_file:
                        output_path = acct / output_file
                        if output_path.exists() and output_path.stat().st_size >= 200:
                            continue  # Already generated with real content — skip
                    log.info(
                        f"[watcher] startup: queuing {skill_name} for {account_name} "
                        f"(output missing or skeleton)"
                    )
                    await self.queue.put(
                        account_name=account_name,
                        skill_name=skill_name,
                        priority=PRIORITY_HIGH,
                        trigger=f"startup:{filename}",
                    )
                    queued += 1

            if queued:
                log.info(f"[watcher] startup scan: {queued} skill(s) queued for {account_name}")
            else:
                log.info(f"[watcher] startup scan: {account_name} all outputs present — nothing to queue")

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
        if not self._loop or self._loop.is_closed():
            log.error(f"[watcher] Event loop dead — dropping event for {path.name}")
            return
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

    def _loop_detected(self, account_name: str, filename: str) -> bool:
        """Return True if this (account, file) has been triggered too many times recently."""
        key = f"{account_name}::{filename}"
        now = time.time()
        history = [t for t in self._trigger_history.get(key, []) if now - t < self.LOOP_WINDOW]
        if len(history) >= self.LOOP_MAX_TRIGGERS:
            log.warning(
                f"[watcher] ⚠ Loop guard: {account_name}/{filename} triggered "
                f"{len(history)}x in {self.LOOP_WINDOW}s — suppressing"
            )
            return True
        history.append(now)
        self._trigger_history[key] = history
        return False

    async def _handle_file(self, path: Path, is_new: bool) -> None:
        filename = path.name
        account_name = path.parent.name

        # 1. Source file changed → queue skills directly
        if filename in FILE_TRIGGERS:
            # Cycle guard: skip if KnowledgeMerger wrote this file itself
            if (
                filename == "discovery.md"
                and self.merger
                and self.merger.was_self_written(account_name)
            ):
                log.debug(f"[watcher] Skipping self-written discovery.md for {account_name} (cycle guard)")
                return
            # Loop detection: suppress if same file triggered too many times recently
            if self._loop_detected(account_name, filename):
                return
            log.info(f"[watcher] Source changed: {account_name}/{filename}")
            await self._enqueue_triggers(account_name, filename)
            return

        # 2. New ingestible file dropped → extract intel → merge to discovery.md
        if (
            path.suffix in INGESTIBLE_EXTENSIONS
            and filename not in JARVIS_OUTPUT_FILES
            and self.extractor
            and self.merger
        ):
            # Ingest cooldown: don't re-process the same file within 5 minutes
            path_key = str(path)
            last_ingest = self._ingest_cooldown.get(path_key, 0)
            if time.time() - last_ingest < self.INGEST_COOLDOWN:
                log.debug(f"[watcher] {filename} recently ingested — skipping")
                return
            self._ingest_cooldown[path_key] = time.time()
            self._seen_files.add(path_key)
            log.info(f"[watcher] New/modified file: {account_name}/{filename} — ingesting")
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
