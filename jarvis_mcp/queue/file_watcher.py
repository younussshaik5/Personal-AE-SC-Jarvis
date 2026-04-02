"""
File watcher — monitors ACCOUNTS/ for changes and queues relevant skills.

Uses watchdog (OS-level file system events) for instant detection.
Falls back to polling if watchdog is unavailable.

When a source file is modified, looks up FILE_TRIGGERS and enqueues
all matching skills with HIGH priority.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict

from .skill_queue import SkillQueue, PRIORITY_HIGH
from .dependency_graph import FILE_TRIGGERS, SKIP_AUTO_QUEUE

log = logging.getLogger(__name__)

DEBOUNCE = 2.0  # seconds — ignore re-triggers for the same file within this window


class FileWatcher:
    """
    Watches ACCOUNTS/ directory for source file changes.
    Fires skill queue events on change via watchdog or polling fallback.
    """

    def __init__(self, queue: SkillQueue, accounts_root: Path):
        self.queue = queue
        self.accounts_root = accounts_root
        self._last_trigger: Dict[str, float] = {}  # "account::file" → last trigger time
        self._running = False
        self._observer = None
        self._task: asyncio.Task = None
        self._loop: asyncio.AbstractEventLoop = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._loop = asyncio.get_event_loop()

        try:
            self._start_watchdog()
        except ImportError:
            log.warning("[watcher] watchdog not available — falling back to polling")
            self._task = asyncio.ensure_future(self._poll())

        log.info(f"[watcher] Watching {self.accounts_root}")

    def stop(self) -> None:
        self._running = False
        if self._observer:
            self._observer.stop()
            self._observer.join()
        if self._task:
            self._task.cancel()
        log.info("[watcher] Stopped")

    # ── Watchdog path ─────────────────────────────────────────────────────────

    def _start_watchdog(self) -> None:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        watcher = self

        class Handler(FileSystemEventHandler):
            def on_modified(self, event):
                if not event.is_directory:
                    watcher._on_file_event(Path(event.src_path))

            def on_created(self, event):
                if not event.is_directory:
                    watcher._on_file_event(Path(event.src_path))

        self._observer = Observer()
        self._observer.schedule(Handler(), str(self.accounts_root), recursive=True)
        self._observer.start()

    def _on_file_event(self, path: Path) -> None:
        """Called by watchdog thread — bridge to asyncio loop."""
        if path.name not in FILE_TRIGGERS:
            return

        # account_name = immediate parent directory name
        account_name = path.parent.name

        key = f"{account_name}::{path.name}"
        now = time.time()
        if now - self._last_trigger.get(key, 0) < DEBOUNCE:
            return
        self._last_trigger[key] = now

        log.info(f"[watcher] Changed: {account_name}/{path.name}")

        # Schedule coroutine safely from watchdog's thread
        asyncio.run_coroutine_threadsafe(
            self._enqueue_triggers(account_name, path.name),
            self._loop,
        )

    # ── Polling fallback ──────────────────────────────────────────────────────

    async def _poll(self) -> None:
        mtimes: Dict[str, float] = {}
        while self._running:
            try:
                if self.accounts_root.exists():
                    for acct_dir in self.accounts_root.iterdir():
                        if not acct_dir.is_dir():
                            continue
                        scan_dirs = [acct_dir] + [d for d in acct_dir.iterdir() if d.is_dir()]
                        for scan_dir in scan_dirs:
                            for fname in FILE_TRIGGERS:
                                fp = scan_dir / fname
                                if not fp.exists():
                                    continue
                                key = f"{scan_dir.name}::{fname}"
                                try:
                                    mtime = fp.stat().st_mtime
                                except OSError:
                                    continue
                                if mtime > mtimes.get(key, 0):
                                    mtimes[key] = mtime
                                    now = time.time()
                                    if now - self._last_trigger.get(key, 0) >= DEBOUNCE:
                                        self._last_trigger[key] = now
                                        log.info(f"[watcher/poll] Changed: {scan_dir.name}/{fname}")
                                        await self._enqueue_triggers(scan_dir.name, fname)
            except Exception as e:
                log.error(f"[watcher/poll] Error: {e}")
            await asyncio.sleep(3.0)

    # ── Shared enqueue logic ──────────────────────────────────────────────────

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
