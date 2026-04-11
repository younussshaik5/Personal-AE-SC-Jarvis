"""
Priority skill queue with deduplication.

Jobs are ordered by priority (lower = sooner).
Duplicate (account_name, skill_name) pairs are ignored — no re-queuing
if a skill is already waiting to run for the same account.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Set, Tuple

log = logging.getLogger(__name__)

PRIORITY_HIGH   = 2   # direct file-change trigger
PRIORITY_MEDIUM = 3   # first-wave cascade
PRIORITY_LOW    = 4   # second-wave cascade
PRIORITY_TAIL   = 5   # third-wave cascade (SOW, meeting_prep from demo)


@dataclass(order=True)
class QueueJob:
    priority:     int          # sort key
    queued_at:    float        # tiebreaker (FIFO within same priority)
    account_name: str  = field(compare=False)
    skill_name:   str  = field(compare=False)
    trigger:      str  = field(compare=False)  # what caused this job (for logging)


class SkillQueue:
    """
    Thread-safe priority queue for skill jobs.
    Deduplicates: if (account, skill) is already queued, the new job is dropped.
    """

    MAX_SIZE = 500  # hard cap — prevents runaway cascade from filling memory

    def __init__(self):
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=self.MAX_SIZE)
        self._pending: Set[Tuple[str, str]] = set()   # (account_name, skill_name)
        self._lock = asyncio.Lock()

    async def put(
        self,
        account_name: str,
        skill_name: str,
        priority: int = PRIORITY_HIGH,
        trigger: str = "unknown",
    ) -> bool:
        """
        Enqueue a skill job. Returns True if queued, False if already pending.
        """
        key = (account_name, skill_name)
        async with self._lock:
            if key in self._pending:
                log.debug(f"[queue] skip duplicate: {skill_name} for {account_name}")
                return False
            if self._queue.qsize() >= self.MAX_SIZE:
                log.error(f"[queue] FULL ({self.MAX_SIZE}) — dropping {skill_name} for {account_name}")
                return False
            self._pending.add(key)

        job = QueueJob(
            priority=priority,
            queued_at=time.monotonic(),
            account_name=account_name,
            skill_name=skill_name,
            trigger=trigger,
        )
        await self._queue.put(job)
        log.info(f"[queue] +{skill_name} | {account_name} | p={priority} | via {trigger}")
        return True

    async def get(self) -> QueueJob:
        """Block until a job is available, then return it."""
        return await self._queue.get()

    async def done(self, job: QueueJob) -> None:
        """Mark a job as processed so it can be re-queued later if needed."""
        key = (job.account_name, job.skill_name)
        async with self._lock:
            self._pending.discard(key)
        self._queue.task_done()

    @property
    def size(self) -> int:
        return self._queue.qsize()

    def pending_for(self, account_name: str) -> list:
        return [s for (a, s) in self._pending if a == account_name]
