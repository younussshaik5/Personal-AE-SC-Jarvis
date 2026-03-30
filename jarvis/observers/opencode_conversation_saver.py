#!/usr/bin/env python3
"""
OpenCode Conversation Saver — persists OpenCode chat to account intel.

Subscribes to `conversation.message` events from ConversationObserver.
Determines the account from `workspace_dir` (expects path under ACCOUNTS/<account>/).
Writes:
- INTEL/conversation_log.md
- activities.jsonl
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event
from jarvis.utils.config import ConfigManager


class OpenCodeConversationSaver:
    """Save OpenCode conversations to account folders."""

    def __init__(self, config_manager: ConfigManager, event_bus: EventBus):
        self.config = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("opencode_conversation_saver")
        self._running = False
        self._workspace_root: Optional[Path] = None
        self._accounts_dir: Optional[Path] = None

    async def start(self):
        """Start the saver."""
        self._running = True
        self._workspace_root = Path(self.config.workspace_root).resolve()
        self._accounts_dir = self._workspace_root / "ACCOUNTS"
        # Ensure accounts dir exists
        self._accounts_dir.mkdir(parents=True, exist_ok=True)

        # Subscribe to conversation events
        self.event_bus.subscribe("conversation.message", self._on_conversation_message)
        self.logger.info("OpenCode conversation saver started", accounts_dir=str(self._accounts_dir))

    async def stop(self):
        """Stop the saver."""
        self._running = False
        self.logger.info("OpenCode conversation saver stopped")

    async def _on_conversation_message(self, event: Event):
        """Handle a conversation message from OpenCode."""
        if not self._running:
            return

        data = event.data
        workspace_dir = data.get("workspace_dir", "")
        if not workspace_dir:
            self.logger.warning("Received conversation.message without workspace_dir", event_data=str(data)[:200])
            return

        self.logger.info("Received conversation", workspace_dir=workspace_dir, role=data.get("role"), content_preview=data.get("content", "")[:100])

        try:
            account_name = self._extract_account_name(Path(workspace_dir))
            if not account_name:
                self.logger.warning("Could not extract account from workspace", workspace_dir=workspace_dir, accounts_dir=str(self._accounts_dir))
                return

            self.logger.info("Processing conversation message", workspace=workspace_dir, account=account_name, role=data.get("role"))
            await self._save_to_account(account_name, data)
        except Exception as e:
            self.logger.error("Failed to process conversation message", error=str(e), workspace_dir=workspace_dir)

    def _extract_account_name(self, workspace_path: Path) -> Optional[str]:
        """Extract account name from workspace path.

        Expects path pattern: ACCOUNTS/<account_name>/... or ACCOUNTS/<team>/<account_name>/...
        If multiple segments, we take the first-level subfolder under ACCOUNTS that exists.
        """
        try:
            # Resolve relative to accounts_dir
            rel = workspace_path.resolve().relative_to(self._accounts_dir.resolve())
            # rel.parts[0] is the top-level folder under ACCOUNTS (often the account name)
            candidate = rel.parts[0]
            # Verify that this folder actually exists (might be a team folder containing account subfolders)
            candidate_path = self._accounts_dir / candidate
            if candidate_path.is_dir():
                return candidate
        except ValueError:
            # Not under ACCOUNTS/ directly - could be nested; try to find any matching account dir
            pass

        # Fallback: scan accounts_dir for a folder that is a prefix of the workspace_path
        for account_dir in self._accounts_dir.iterdir():
            if account_dir.is_dir():
                try:
                    workspace_path.resolve().relative_to(account_dir.resolve())
                    return account_dir.name
                except ValueError:
                    continue
        return None

    async def _save_to_account(self, account_name: str, data: dict):
        """Append conversation to account's intel log and activities."""
        account_dir = self._accounts_dir / account_name
        if not account_dir.exists():
            self.logger.warning("Account directory not found", account=account_name, path=str(account_dir))
            return

        # Prepare paths
        intel_dir = account_dir / "INTEL"
        intel_dir.mkdir(parents=True, exist_ok=True)
        conv_log = intel_dir / "conversation_log.md"

        activities_file = account_dir / "activities.jsonl"

        # Parse timestamp (handle seconds or milliseconds)
        ts_val = data.get("timestamp")
        try:
            if isinstance(ts_val, (int, float)):
                # If timestamp is in milliseconds (common in many systems), convert to seconds
                if ts_val > 1e12:  # heuristic: > 1 trillion implies milliseconds since epoch
                    ts_val = ts_val / 1000.0
                dt = datetime.fromtimestamp(ts_val)
            else:
                # Try to parse as ISO string
                dt = datetime.fromisoformat(str(ts_val).replace("Z", "+00:00"))
        except Exception as e:
            self.logger.warning("Failed to parse timestamp, using now", raw_ts=ts_val, error=str(e))
            dt = datetime.now()
        ts_str = dt.strftime("%Y-%m-%d %H:%M")

        role = data.get("role", "unknown")
        content = data.get("content", "").strip()

        if not content:
            return

        # Append to conversation_log.md
        try:
            with open(conv_log, "a", encoding="utf-8") as f:
                f.write(f"\n## {ts_str} — {role.title()}\n\n{content}\n\n---\n")
        except Exception as e:
            self.logger.error("Failed to write conversation_log.md", error=str(e))

        # Append to activities.jsonl
        try:
            entry = {
                "timestamp": ts_str,
                "source": "opencode_conversation",
                "summary": content[:200],
                "role": role,
                "workspace_dir": data.get("workspace_dir", "")
            }
            with open(activities_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            self.logger.error("Failed to write activities.jsonl", error=str(e))

        self.logger.info("Saved conversation to account", account=account_name, role=role)
