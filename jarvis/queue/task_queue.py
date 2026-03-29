#!/usr/bin/env python3
"""
JARVIS Task Queue — SQLite-backed, persistent, deduplicated.

Why SQLite instead of RabbitMQ/Kafka:
  - Zero extra services to install or start
  - Tasks survive JARVIS restarts (persistent on disk)
  - Simple enough for a single-machine setup
  - Same deduplication and ordering guarantees needed here

Priority levels:
  1 = HIGH   — meetings, recordings, brain entries (process immediately)
  2 = MEDIUM — documents, emails, stage changes (process within 1 min)
  3 = LOW    — gap fills, pattern synthesis, html refresh (process when idle)

Deduplication:
  Same (task_type, account, dedup_key) won't be queued twice if already pending.
  Prevents 100 "gap_fill:AcmeCorp" tasks from piling up when files change rapidly.
"""

import asyncio
import json
import sqlite3
import time
import uuid
from enum import IntEnum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from jarvis.utils.logger import JARVISLogger


class TaskPriority(IntEnum):
    HIGH   = 1
    MEDIUM = 2
    LOW    = 3


class Task:
    __slots__ = ("id", "type", "account", "dedup_key", "payload",
                 "priority", "status", "created_at", "retries", "max_retries")

    def __init__(self, type: str, payload: Dict[str, Any],
                 account: str = "", dedup_key: str = "",
                 priority: TaskPriority = TaskPriority.MEDIUM,
                 max_retries: int = 3):
        self.id        = str(uuid.uuid4())
        self.type      = type
        self.account   = account
        self.dedup_key = dedup_key or f"{type}:{account}"
        self.payload   = payload
        self.priority  = int(priority)
        self.status    = "pending"
        self.created_at = time.time()
        self.retries   = 0
        self.max_retries = max_retries


class TaskQueue:
    """
    SQLite-backed async task queue.
    Thread-safe via asyncio lock + SQLite WAL mode.
    """

    DB_FILE = "data/task_queue.db"

    def __init__(self, jarvis_home: Path):
        self.db_path = jarvis_home / self.DB_FILE
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = JARVISLogger("queue.task_queue")
        self._lock = asyncio.Lock()
        self._notify = asyncio.Event()  # workers wait on this
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id          TEXT PRIMARY KEY,
                    type        TEXT NOT NULL,
                    account     TEXT NOT NULL DEFAULT '',
                    dedup_key   TEXT NOT NULL DEFAULT '',
                    payload     TEXT NOT NULL DEFAULT '{}',
                    priority    INTEGER NOT NULL DEFAULT 2,
                    status      TEXT NOT NULL DEFAULT 'pending',
                    created_at  REAL NOT NULL,
                    retries     INTEGER NOT NULL DEFAULT 0,
                    max_retries INTEGER NOT NULL DEFAULT 3
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status_priority ON tasks(status, priority, created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_dedup ON tasks(dedup_key, status)")
            conn.commit()

    async def enqueue(
        self,
        task_type: str,
        payload: Dict[str, Any],
        account: str = "",
        dedup_key: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        max_retries: int = 3,
    ) -> Optional[str]:
        """
        Add a task to the queue.
        Returns task id, or None if deduplicated (already pending).
        """
        dk = dedup_key or f"{task_type}:{account}"
        task = Task(task_type, payload, account, dk, priority, max_retries)

        async with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                # Deduplication: if same dedup_key is already pending, skip
                row = conn.execute(
                    "SELECT id FROM tasks WHERE dedup_key=? AND status='pending'",
                    (dk,)
                ).fetchone()
                if row:
                    self.logger.debug("Task deduplicated", type=task_type, account=account)
                    return None

                conn.execute("""
                    INSERT INTO tasks (id, type, account, dedup_key, payload, priority, status, created_at, retries, max_retries)
                    VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, 0, ?)
                """, (task.id, task.type, task.account, task.dedup_key,
                      json.dumps(task.payload), task.priority, task.created_at, task.max_retries))
                conn.commit()

        self.logger.debug("Task queued", type=task_type, account=account, priority=priority)
        self._notify.set()  # wake up workers
        return task.id

    async def dequeue(self) -> Optional[Task]:
        """
        Pull the highest-priority pending task and mark it in_progress.
        Returns None if queue is empty.
        """
        async with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute("""
                    SELECT id, type, account, dedup_key, payload, priority, created_at, retries, max_retries
                    FROM tasks
                    WHERE status='pending'
                    ORDER BY priority ASC, created_at ASC
                    LIMIT 1
                """).fetchone()

                if not row:
                    return None

                task_id, ttype, account, dk, payload_json, prio, created_at, retries, max_retries = row
                conn.execute("UPDATE tasks SET status='in_progress' WHERE id=?", (task_id,))
                conn.commit()

            t = Task.__new__(Task)
            t.id          = task_id
            t.type        = ttype
            t.account     = account
            t.dedup_key   = dk
            t.payload     = json.loads(payload_json)
            t.priority    = prio
            t.status      = "in_progress"
            t.created_at  = created_at
            t.retries     = retries
            t.max_retries = max_retries
            return t

    async def complete(self, task_id: str):
        """Mark task as done and remove it."""
        async with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
                conn.commit()

    async def fail(self, task_id: str, error: str):
        """Mark task failed. Re-queue with lower priority if retries remain."""
        async with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute(
                    "SELECT retries, max_retries, priority FROM tasks WHERE id=?",
                    (task_id,)
                ).fetchone()
                if not row:
                    return
                retries, max_retries, priority = row
                if retries < max_retries:
                    # Re-queue with backoff — bump to lower priority
                    new_priority = min(priority + 1, int(TaskPriority.LOW))
                    conn.execute("""
                        UPDATE tasks SET status='pending', retries=retries+1, priority=?
                        WHERE id=?
                    """, (new_priority, task_id))
                    self.logger.warning("Task failed, retrying",
                                        task_id=task_id, retry=retries + 1, error=error)
                else:
                    conn.execute("UPDATE tasks SET status='failed' WHERE id=?", (task_id,))
                    self.logger.error("Task permanently failed",
                                      task_id=task_id, error=error)
                conn.commit()

    async def pending_count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE status='pending'"
            ).fetchone()[0]

    async def wait_for_work(self, timeout: float = 5.0):
        """Block until a new task is enqueued or timeout expires."""
        try:
            await asyncio.wait_for(self._notify.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            pass
        finally:
            self._notify.clear()

    async def cleanup_old(self, max_age_hours: float = 24.0):
        """Remove completed/failed tasks older than max_age_hours."""
        cutoff = time.time() - (max_age_hours * 3600)
        async with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "DELETE FROM tasks WHERE status IN ('completed','failed') AND created_at < ?",
                    (cutoff,)
                )
                conn.commit()

    async def stats(self) -> Dict[str, int]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) FROM tasks GROUP BY status"
            ).fetchall()
        return {status: count for status, count in rows}
