#!/usr/bin/env python3
"""File System Observer - monitors workspace for changes using watchdog."""

import asyncio
import json
import os
from pathlib import Path
from typing import Set, Dict, Optional, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event


class JarvisFileSystemEventHandler(FileSystemEventHandler):
    """Handles file system events and publishes them to event bus."""

    def __init__(self, event_bus: EventBus, workspace_path: Path, main_loop: asyncio.AbstractEventLoop, ignore_patterns: Set[str]):
        self.event_bus = event_bus
        self.workspace = workspace_path
        self.logger = JARVISLogger("file_system")
        self.ignore_patterns = ignore_patterns
        self.main_loop = main_loop

    def on_created(self, event: FileSystemEvent):
        if self._should_ignore(event.src_path):
            return
        self._publish_event("file.created", event.src_path, event.is_directory)

    def on_modified(self, event: FileSystemEvent):
        if self._should_ignore(event.src_path):
            return
        self._publish_event("file.modified", event.src_path, event.is_directory)

    def on_deleted(self, event: FileSystemEvent):
        if self._should_ignore(event.src_path):
            return
        self._publish_event("file.deleted", event.src_path, event.is_directory)

    def on_moved(self, event: FileSystemEvent):
        if self._should_ignore(event.src_path) or self._should_ignore(event.dest_path):
            return
        self._publish_event("file.moved", event.src_path, event.is_directory, {
            "dest": event.dest_path
        })

    def _should_ignore(self, path: Any) -> bool:
        # Convert path to string if bytes
        if isinstance(path, bytes):
            path = path.decode('utf-8', errors='ignore')
        p = Path(path)
        try:
            rel = p.relative_to(self.workspace) if self.workspace in p.parents else p
        except ValueError:
            # path not relative to workspace, skip
            return False
        return any(part in self.ignore_patterns for part in rel.parts)

    def _publish_event(self, event_type: str, path: Any, is_dir: bool, extra: Optional[dict] = None):
        # Convert path to string if bytes
        if isinstance(path, bytes):
            path = path.decode('utf-8', errors='ignore')
        # Run publish in thread-safe manner using the main loop
        self.main_loop.call_soon_threadsafe(
            self.event_bus.publish,
            Event(event_type, "file_system", {
                "path": str(path),
                "is_directory": is_dir,
                **(extra or {})
            })
        )


class FileSystemObserver:
    """Watches file system for changes and emits events."""

    def __init__(self, config, event_bus: EventBus):
        self.config = config
        self.event_bus = event_bus
        self.logger = JARVISLogger("file_system")
        self.observer = Observer()
        self.handlers: list[JarvisFileSystemEventHandler] = []
        self._workspaces: Set[Path] = set()
        self._main_loop: asyncio.AbstractEventLoop = None  # type: ignore
        # State persistence for backfill
        self.state_file = Path('MEMORY/state/file_system_observer.json')
        self._known_files: Dict[str, dict] = {}  # path -> {'is_dir': bool, 'mtime': float}
        # Ignore patterns (consistent across all handlers)
        self.ignore_patterns = {'.git', '__pycache__', '.jarvis', 'node_modules', '.pytest_cache', 'MEMORY/state', 'logs'}

    async def start(self):
        """Start watching configured workspaces."""
        self.logger.info("Starting file system observer")
        # Load persisted state for backfill
        await self._load_state()
        # Subscribe to file events to maintain state
        self.event_bus.subscribe("file.created", self._on_file_created)
        self.event_bus.subscribe("file.modified", self._on_file_modified)
        self.event_bus.subscribe("file.deleted", self._on_file_deleted)
        self.event_bus.subscribe("file.moved", self._on_file_moved)
        # Get main loop
        self._main_loop = asyncio.get_event_loop()
        # Watch workspace root
        workspaces = [Path(self.config.workspace_root).resolve()]
        for ws in workspaces:
            if ws.exists():
                handler = JarvisFileSystemEventHandler(self.event_bus, ws, self._main_loop, self.ignore_patterns)
                self.observer.schedule(handler, str(ws), recursive=True)
                self.handlers.append(handler)
                self._workspaces.add(ws)
                self.logger.debug("Watching workspace", path=str(ws))
        # Also watch CLAUDE_SPACE directory (where Claude conversations happen)
        claude_space = Path(os.environ.get(
            "CLAUDE_SPACE",
            str(Path.home() / "Documents" / "claude space")
        )).resolve()
        if claude_space.exists() and claude_space not in self._workspaces:
            cs_handler = JarvisFileSystemEventHandler(
                self.event_bus, claude_space, self._main_loop, self.ignore_patterns
            )
            self.observer.schedule(cs_handler, str(claude_space), recursive=True)
            self.handlers.append(cs_handler)
            self._workspaces.add(claude_space)
            self.logger.info("Watching claude space", path=str(claude_space))

        self.observer.start()
        self.logger.info("File system observer started", workspaces_count=len(self._workspaces))
        # Perform initial backfill scan to catch missed changes
        asyncio.create_task(self._initial_scan())

    async def stop(self):
        """Stop watching."""
        self.observer.stop()
        self.observer.join()
        await self._save_state()
        self.logger.info("File system observer stopped")

    def add_workspace(self, path: Path):
        """Dynamically add a workspace to watch."""
        if path.exists() and path not in self._workspaces:
            handler = JarvisFileSystemEventHandler(self.event_bus, path, self._main_loop, self.ignore_patterns)
            self.observer.schedule(handler, str(path), recursive=True)
            self.handlers.append(handler)
            self._workspaces.add(path)

    async def _load_state(self):
        """Load known files from state file."""
        try:
            if self.state_file.exists():
                with open(self.state_file) as f:
                    state = json.load(f)
                    self._known_files = state.get('known_files', {})
                self.logger.info("Loaded file system observer state", known_files_count=len(self._known_files))
            else:
                self._known_files = {}
                self.logger.info("No previous state found, starting fresh")
        except Exception as e:
            self.logger.error("Failed to load state", error=str(e))
            self._known_files = {}

    async def _save_state(self):
        """Save known files to state file."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump({'known_files': self._known_files}, f, indent=2)
        except Exception as e:
            self.logger.error("Failed to save state", error=str(e))

    # State update handlers - called when our own events are published
    async def _on_file_created(self, event: Event):
        path = event.data['path']
        is_dir = event.data['is_directory']
        mtime = event.data.get('mtime')
        if mtime is None:
            try:
                mtime = Path(path).stat().st_mtime
            except:
                mtime = 0
        self._known_files[path] = {'is_dir': is_dir, 'mtime': mtime}

    async def _on_file_modified(self, event: Event):
        path = event.data['path']
        is_dir = event.data['is_directory']
        mtime = event.data.get('mtime')
        if mtime is None:
            try:
                mtime = Path(path).stat().st_mtime
            except:
                mtime = 0
        if path in self._known_files:
            self._known_files[path].update({'is_dir': is_dir, 'mtime': mtime})
        else:
            self._known_files[path] = {'is_dir': is_dir, 'mtime': mtime}

    async def _on_file_deleted(self, event: Event):
        path = event.data['path']
        if path in self._known_files:
            del self._known_files[path]

    async def _on_file_moved(self, event: Event):
        old_path = event.data['path']
        new_path = event.data['dest']
        if old_path in self._known_files:
            data = self._known_files.pop(old_path)
            self._known_files[new_path] = data

    async def _initial_scan(self):
        """Scan all workspaces and backfill events for changes since last run."""
        self.logger.info("Starting initial backfill scan")
        # Temporarily unsubscribe state handlers to avoid double updates
        self.event_bus.unsubscribe("file.created", self._on_file_created)
        self.event_bus.unsubscribe("file.modified", self._on_file_modified)
        self.event_bus.unsubscribe("file.deleted", self._on_file_deleted)
        self.event_bus.unsubscribe("file.moved", self._on_file_moved)
        try:
            for ws in self._workspaces:
                await self._scan_directory(ws)
        except Exception as e:
            self.logger.error("Initial scan error", error=str(e))
        finally:
            # Re-subscribe state handlers
            self.event_bus.subscribe("file.created", self._on_file_created)
            self.event_bus.subscribe("file.modified", self._on_file_modified)
            self.event_bus.subscribe("file.deleted", self._on_file_deleted)
            self.event_bus.subscribe("file.moved", self._on_file_moved)
            # Save state after scan completes
            await self._save_state()
        self.logger.info("Initial backfill scan completed")

    async def _scan_directory(self, directory: Path):
        """Recursively scan directory and emit events for differences."""
        try:
            current_paths = set()
            for path in directory.rglob('*'):
                try:
                    # Skip if should be ignored (any component matches ignore_patterns)
                    try:
                        rel_parts = path.relative_to(directory).parts
                    except ValueError:
                        continue
                    if any(part in self.ignore_patterns for part in rel_parts):
                        continue
                    if path.is_symlink():
                        continue

                    stat = path.stat()
                    mtime = stat.st_mtime
                    is_dir = path.is_dir()

                    abs_path = str(path.resolve())
                    current_paths.add(abs_path)

                    if abs_path not in self._known_files:
                        # New file/directory - emit created event
                        self.logger.debug("Backfill: new file", path=abs_path)
                        self.event_bus.publish(Event("file.created", "file_system", {
                            "path": abs_path,
                            "is_directory": is_dir,
                            "mtime": mtime
                        }))
                        self._known_files[abs_path] = {'is_dir': is_dir, 'mtime': mtime}
                    else:
                        known = self._known_files[abs_path]
                        if known['mtime'] != mtime or known['is_dir'] != is_dir:
                            # Modified - emit modified event
                            self.logger.debug("Backfill: modified file", path=abs_path)
                            self.event_bus.publish(Event("file.modified", "file_system", {
                                "path": abs_path,
                                "is_directory": is_dir,
                                "mtime": mtime
                            }))
                            known['mtime'] = mtime
                            known['is_dir'] = is_dir
                except (OSError, PermissionError) as e:
                    self.logger.debug("Scan error", path=str(path), error=str(e))
                    continue

            # Check for deleted files (in state but not on disk)
            dir_resolved = str(directory.resolve())
            for abs_path in list(self._known_files.keys()):
                if abs_path.startswith(dir_resolved) and abs_path not in current_paths:
                    # File deleted since last run
                    self.logger.debug("Backfill: deleted file", path=abs_path)
                    is_dir = self._known_files[abs_path]['is_dir']
                    self.event_bus.publish(Event("file.deleted", "file_system", {
                        "path": abs_path,
                        "is_directory": is_dir
                    }))
                    del self._known_files[abs_path]
        except Exception as e:
            self.logger.error("Scan directory error", directory=str(directory), error=str(e))
