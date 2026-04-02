"""
Queue worker — consumes skill jobs from SkillQueue and runs them.

After each skill completes, checks SKILL_CASCADES and queues
any downstream skills automatically.

One worker runs as a background asyncio task.
"""

import asyncio
import logging
import time
from typing import Dict, Any

from .skill_queue import SkillQueue, PRIORITY_MEDIUM, PRIORITY_LOW, PRIORITY_TAIL
from .dependency_graph import SKILL_CASCADES, SKIP_AUTO_QUEUE

log = logging.getLogger(__name__)


class QueueWorker:
    """
    Background worker that processes the skill queue.

    Flow per job:
      1. Pull job from queue
      2. Run skill.generate(account_name)
      3. On success → record in SelfLearner + cascade downstream skills
      4. On failure → log, mark done, continue (no crash)
    """

    def __init__(self, queue: SkillQueue, skills: Dict[str, Any], learner=None):
        self.queue   = queue
        self.skills  = skills   # SKILL_REGISTRY instances from JarvisServer
        self.learner = learner  # Optional SelfLearner — set after init
        self._running = False
        self._task: asyncio.Task = None

    def start(self, loop: asyncio.AbstractEventLoop = None) -> None:
        """Start the worker as a background asyncio task."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.ensure_future(self._run())
        log.info("[worker] Queue worker started")

    def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
        log.info("[worker] Queue worker stopped")

    async def _run(self) -> None:
        """Main loop — process jobs until stopped."""
        while self._running:
            try:
                job = await asyncio.wait_for(self.queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            await self._process(job)

    async def _process(self, job) -> None:
        skill = self.skills.get(job.skill_name)
        if not skill:
            log.warning(f"[worker] Unknown skill: {job.skill_name} — skipping")
            await self.queue.done(job)
            return

        t0 = time.time()
        log.info(f"[worker] ▶ {job.skill_name} | {job.account_name} | trigger={job.trigger}")

        try:
            result = await skill.generate(job.account_name)
            elapsed = round(time.time() - t0, 1)

            if result and result.strip().startswith("❌"):
                log.warning(f"[worker] ✗ {job.skill_name} | {job.account_name} | {elapsed}s | LLM error")
                if self.learner:
                    await self.learner.record(job.account_name, job.skill_name, job.trigger, status="error")
            else:
                log.info(f"[worker] ✓ {job.skill_name} | {job.account_name} | {elapsed}s")
                if self.learner:
                    await self.learner.record(job.account_name, job.skill_name, job.trigger, status="ok")
                await self._cascade(job)

        except Exception as e:
            elapsed = round(time.time() - t0, 1)
            log.error(f"[worker] ✗ {job.skill_name} | {job.account_name} | {elapsed}s | {e}")

        finally:
            await self.queue.done(job)

    async def _cascade(self, completed_job) -> None:
        """Queue downstream skills after a skill completes successfully."""
        await self.trigger_cascade(completed_job.account_name, completed_job.skill_name)

    async def trigger_cascade(self, account_name: str, skill_name: str) -> None:
        """
        Public method — trigger cascade for a skill that just completed.
        Call this after a user-triggered skill succeeds to fire the same
        downstream chain as the queue worker would.
        """
        cascade = SKILL_CASCADES.get(skill_name)
        if not cascade:
            return

        priority = cascade.get("priority", PRIORITY_LOW)
        for downstream_skill in cascade["skills"]:
            if downstream_skill in SKIP_AUTO_QUEUE:
                continue
            await self.queue.put(
                account_name=account_name,
                skill_name=downstream_skill,
                priority=priority,
                trigger=f"cascade:{skill_name}",
            )
