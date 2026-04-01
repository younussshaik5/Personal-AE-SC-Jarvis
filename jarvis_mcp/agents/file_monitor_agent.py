"""File Monitor Agent - watches for document changes in account folders."""

import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Callable, Optional
import json


class FileMonitorAgent:
    """Monitors account folders for file changes and triggers ingestion."""

    def __init__(self, account_path: str):
        """Initialize file monitor for an account."""
        self.account_path = Path(account_path)
        self.watched_extensions = {".pdf", ".xlsx", ".pptx", ".docx", ".txt", ".json"}
        self.state_file = self.account_path / ".file_monitor_state.json"
        self.monitored_files = self._load_state()

    def _load_state(self) -> Dict[str, Dict[str, Any]]:
        """Load previous file state."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_state(self):
        """Save current file state."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.monitored_files, f, indent=2)
        except Exception as e:
            print(f"Error saving monitor state: {e}")

    async def scan_for_changes(self) -> List[Dict[str, Any]]:
        """Scan account folders for new or changed files."""
        new_files = []

        # Walk through account directory
        for file_path in self.account_path.rglob("*"):
            if not file_path.is_file():
                continue

            # Check file extension
            if file_path.suffix.lower() not in self.watched_extensions:
                continue

            # Get file stats
            stat = file_path.stat()
            file_key = str(file_path)

            # Check if new or modified
            if file_key not in self.monitored_files:
                new_files.append({
                    "path": str(file_path),
                    "type": "new",
                    "extension": file_path.suffix.lower(),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
                self.monitored_files[file_key] = {
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                    "processed": False
                }
            elif stat.st_mtime > self.monitored_files[file_key].get("mtime", 0):
                new_files.append({
                    "path": str(file_path),
                    "type": "modified",
                    "extension": file_path.suffix.lower(),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
                self.monitored_files[file_key]["mtime"] = stat.st_mtime
                self.monitored_files[file_key]["processed"] = False

        self._save_state()
        return new_files

    async def mark_processed(self, file_path: str):
        """Mark a file as processed."""
        file_key = str(Path(file_path))
        if file_key in self.monitored_files:
            self.monitored_files[file_key]["processed"] = True
            self._save_state()

    async def get_unprocessed_files(self) -> List[str]:
        """Get list of unprocessed files."""
        unprocessed = []
        for file_path, state in self.monitored_files.items():
            if not state.get("processed", False) and Path(file_path).exists():
                unprocessed.append(file_path)
        return unprocessed

    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        return {
            "watching_path": str(self.account_path),
            "watched_extensions": list(self.watched_extensions),
            "total_files_monitored": len(self.monitored_files),
            "unprocessed_files": len([s for s in self.monitored_files.values() if not s.get("processed", False)])
        }
