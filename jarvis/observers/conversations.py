#!/usr/bin/env python3
"""Conversation Observer - monitors OpenCode conversations via DB polling."""

import asyncio
import sqlite3
import json
from pathlib import Path
from typing import Any, Optional
from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event


class ConversationObserver:
    """Polls OpenCode database for new conversation messages."""

    def __init__(self, config, event_bus: EventBus):
        self.config = config
        self.event_bus = event_bus
        self.logger = JARVISLogger("conversations")
        self.db_path = config.opencode_db_path
        self._last_seen: int = 0
        self._polling_task: Optional[asyncio.Task] = None
        self._running = False
        # Workspace filtering: only learn from this workspace's sessions
        self.workspace_root = Path(config.workspace_root).resolve()
        self._allowed_workspace_prefix = str(self.workspace_root) + "/"
        # State persistence for backfill
        self.state_file = Path('MEMORY/state/conversation_observer.json')

    async def start(self):
        """Start polling the OpenCode database."""
        self.logger.info("Starting conversation observer", db=str(self.db_path))
        if not self.db_path.exists():
            self.logger.warning("OpenCode DB not found, conversation observer disabled")
            return

        # Load persisted state
        await self._load_state()

        self._running = True
        self._polling_task = asyncio.create_task(self._poll_loop())

    async def _load_state(self):
        """Load last_seen from state file."""
        try:
            if self.state_file.exists():
                with open(self.state_file) as f:
                    state = json.load(f)
                    self._last_seen = state.get('last_seen', 0)
                self.logger.info("Loaded conversation observer state", last_seen=self._last_seen)
            else:
                self._last_seen = 0
                self.logger.info("No previous state found, starting fresh")
        except Exception as e:
            self.logger.error("Failed to load state", error=str(e))
            self._last_seen = 0

    async def _save_state(self):
        """Save last_seen to state file."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump({'last_seen': self._last_seen}, f)
        except Exception as e:
            self.logger.error("Failed to save state", error=str(e))

    async def stop(self):
        """Stop the conversation observer."""
        self._running = False
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Conversation observer stopped")

    async def _poll_loop(self):
        """Main polling loop."""
        while self._running:
            try:
                await self._poll_messages()
                await asyncio.sleep(self.config.polling_interval_seconds)
            except Exception as e:
                self.logger.error("Polling error", error=str(e))
                await asyncio.sleep(5)

    async def _poll_messages(self):
        """Query new messages since last poll, filtered by workspace."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            # Join with session table to filter by workspace directory
            cur.execute("""
                SELECT m.id, m.session_id, m.time_created, m.data, s.directory as session_dir
                FROM message m
                JOIN session s ON m.session_id = s.id
                WHERE m.time_created > ?
                  AND s.directory LIKE ?
                ORDER BY m.time_created ASC
            """, (self._last_seen, f"{self._allowed_workspace_prefix}%"))
            rows = cur.fetchall()
            conn.close()

            for row in rows:
                await self._process_message(row)
                if row['time_created'] > self._last_seen:
                    self._last_seen = row['time_created']

            # Save state after successful poll
            await self._save_state()

        except sqlite3.OperationalError as e:
            # DB may be locked or missing
            self.logger.debug("DB operational error", error=str(e))
        except Exception as e:
            self.logger.error("DB query error", error=str(e))

    async def _process_message(self, row: sqlite3.Row):
        """Process a message row and emit event."""
        try:
            data = json.loads(row['data']) if isinstance(row['data'], str) else row['data']
            content = data.get('content') or data.get('text') or ''
            role = data.get('role', 'user')
            model = data.get('model', {}).get('modelID', 'unknown')
            # Also include workspace info
            session_dir = row['session_dir'] if 'session_dir' in row.keys() else None

            event = Event("conversation.message", "conversations", {
                "message_id": row['id'],
                "session_id": row['session_id'],
                "timestamp": row['time_created'],
                "role": role,
                "content": content,
                "model": model,
                "workspace_dir": session_dir  # Include workspace for downstream filtering
            })
            self.event_bus.publish(event)
        except Exception as e:
            self.logger.error("Failed to process message", message_id=row['id'], error=str(e))