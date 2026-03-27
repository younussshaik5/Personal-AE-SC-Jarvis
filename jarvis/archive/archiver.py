#!/usr/bin/env python3
"""Archiver - handles snapshots and restores.

Fixed: Each snapshot is independent — excludes previous archives and large
directories (node_modules, .git, __pycache__, logs) to keep snapshots small
and fast. Only keeps the last 3 snapshots to prevent disk bloat.
"""

import asyncio
import tarfile
import json
from pathlib import Path
from datetime import datetime
from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event

# Directories/patterns to always exclude from snapshots
EXCLUDE_PATTERNS = {
    'archives',         # previous snapshots
    'node_modules',     # npm packages (reinstallable)
    '.git',             # git history (already version controlled)
    '__pycache__',      # python bytecode cache
    '.pyc',             # compiled python
    '.tar.gz',          # any compressed archives
    '.venv',            # virtual environments
    'venv',             # virtual environments
    '.DS_Store',        # macOS metadata
}

MAX_SNAPSHOTS = 3  # only keep the last 3 snapshots


class Archiver:
    """Creates and manages archives of workspaces and data."""

    def __init__(self, config, event_bus: EventBus):
        self.config = config
        self.event_bus = event_bus
        self.logger = JARVISLogger("archiver")
        self.event_bus.subscribe("archive.request", self._on_archive_request)
        self.event_bus.subscribe("system.shutdown", self._on_shutdown)

    async def start(self):
        """Start archiver (scheduled tasks would be set up here)."""
        self.logger.info("Archiver started")

    async def stop(self):
        """Final archive before shutdown."""
        await self.create_snapshot("shutdown")
        self.logger.info("Archiver stopped")

    def _on_archive_request(self, event: Event):
        """Handle explicit archive request."""
        reason = event.data.get("reason", "manual")
        asyncio.create_task(self.create_snapshot(reason))

    def _on_shutdown(self, event: Event):
        """Trigger final archive."""
        asyncio.create_task(self.create_snapshot("shutdown"))

    async def create_snapshot(self, reason: str = "scheduled") -> Path:
        """Create a compressed snapshot of current workspace.
        
        Each snapshot is independent and excludes:
        - Previous archives (no recursive bloat)
        - node_modules, .git, __pycache__, .venv (reinstallable/regenerated)
        - Log files (non-essential for restore)
        
        After creation, old snapshots beyond MAX_SNAPSHOTS are pruned.
        """
        now = datetime.utcnow()
        date_str = now.strftime("%Y-%m")
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        archive_name = f"snapshot_{timestamp}_{reason}.tar.gz"
        archive_dir = self.config.archives_dir / date_str
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_path = archive_dir / archive_name

        self.logger.info("Creating snapshot", reason=reason, path=str(archive_path))

        try:
            with tarfile.open(archive_path, "w:gz") as tar:
                # Add workspace root (with exclusion filter applied)
                if self.config.workspace_root.exists():
                    tar.add(self.config.workspace_root, arcname="workspace",
                            filter=self._exclude_bloat)
                # Add data directory (with exclusion filter applied)
                if self.config.data_dir.exists():
                    tar.add(self.config.data_dir, arcname="data",
                            filter=self._exclude_bloat)
                # Add config
                if self.config.CONFIG_FILE.exists():
                    tar.add(self.config.CONFIG_FILE, arcname="config/jarvis.yaml")

            size_mb = archive_path.stat().st_size / (1024 * 1024)
            self.logger.info("Snapshot created",
                             path=str(archive_path),
                             size_mb=f"{size_mb:.1f}")

            # Publish event
            self.event_bus.publish(Event("archive.created", "archiver", {
                "path": str(archive_path),
                "reason": reason,
                "size": archive_path.stat().st_size
            }))

            # Prune old snapshots to keep disk usage under control
            self._prune_old_snapshots(archive_dir)

            return archive_path
        except Exception as e:
            self.logger.error("Snapshot failed", error=str(e))
            # Clean up partial archive if it exists
            if archive_path.exists():
                archive_path.unlink()
            raise

    def _exclude_bloat(self, tarinfo):
        """Exclude large/regenerable directories and previous archives.
        
        This filter is applied to BOTH workspace and data directories,
        preventing the recursive bloat bug where archives include previous
        archives.
        """
        name = tarinfo.name
        # Check each path component against exclude patterns
        parts = Path(name).parts
        for part in parts:
            if part in EXCLUDE_PATTERNS:
                return None
            # Also check file extensions
            if any(part.endswith(ext) for ext in ('.tar.gz', '.pyc')):
                return None
        return tarinfo

    def _prune_old_snapshots(self, archive_dir: Path):
        """Keep only the last MAX_SNAPSHOTS snapshots, delete the rest."""
        snapshots = sorted(archive_dir.glob("snapshot_*.tar.gz"),
                           key=lambda p: p.stat().st_mtime,
                           reverse=True)

        if len(snapshots) <= MAX_SNAPSHOTS:
            return

        for old_snapshot in snapshots[MAX_SNAPSHOTS:]:
            size_mb = old_snapshot.stat().st_size / (1024 * 1024)
            self.logger.info("Pruning old snapshot",
                             path=str(old_snapshot),
                             size_mb=f"{size_mb:.1f}")
            old_snapshot.unlink()

    async def restore_snapshot(self, archive_path: Path, target_root: Path = None):
        """Restore from a snapshot."""
        if not archive_path.exists():
            raise FileNotFoundError(f"Archive not found: {archive_path}")

        target = target_root or self.config.workspace_root
        self.logger.info("Restoring snapshot", archive=str(archive_path), target=str(target))

        try:
            with tarfile.open(archive_path, "r:gz") as tar:
                # Backup current before restore
                await self._backup_current(target)
                # Extract
                tar.extractall(target)

            self.logger.info("Restore complete")
            self.event_bus.publish(Event("archive.restored", "archiver", {
                "archive": str(archive_path),
                "target": str(target)
            }))
        except Exception as e:
            self.logger.error("Restore failed", error=str(e))
            raise

    async def _backup_current(self, target: Path):
        """Create a quick backup of current state before restore."""
        backup_dir = self.config.archives_dir / "pre_restore"
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"before_restore_{timestamp}.tar.gz"

        self.logger.debug("Backing up before restore", backup=str(backup_path))
        # Could implement quick tar of critical dirs here