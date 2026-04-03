"""
Queue worker — consumes skill jobs from SkillQueue and runs them.

After each skill completes:
  1. Records in SelfLearner (_skill_timeline + _evolution_log)
  2. Feedback loop: extracts new intel from output → merges to discovery.md
     (only for FEEDBACK_SKILLS — meddpicc, risk_report, conversation_extractor, etc.)
  3. Cascades downstream skills (dependency_graph.SKILL_CASCADES)

The feedback loop is what makes JARVIS self-evolving:
  meddpicc output → new intel extracted → discovery.md updated
  → file watcher detects change → cascade fires again with richer context
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional

from .skill_queue import SkillQueue, PRIORITY_MEDIUM, PRIORITY_LOW, PRIORITY_TAIL
from .dependency_graph import SKILL_CASCADES, SKIP_AUTO_QUEUE, SKILL_OUTPUT_FILES

log = logging.getLogger(__name__)


class QueueWorker:
    """
    Background worker that processes the skill queue.

    Flow per job:
      1. Pull job from queue
      2. Run skill.generate(account_name)
      3. Record in SelfLearner
      4. Feedback: extract intel from output → merge to discovery.md
      5. Cascade downstream skills
    """

    def __init__(
        self,
        queue: SkillQueue,
        skills: Dict[str, Any],
        learner=None,
        extractor=None,   # IntelligenceExtractor
        merger=None,      # KnowledgeMerger
    ):
        self.queue     = queue
        self.skills    = skills
        self.learner   = learner
        self.extractor = extractor
        self.merger    = merger
        self._running  = False
        self._task: asyncio.Task = None
        # Dedup: track recently completed (account::skill) → timestamp
        self._recent_runs: Dict[str, float] = {}
        self.RECENT_RUN_WINDOW = 300  # 5 min — don't re-run same skill via cascade

    def start(self) -> None:
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
        SKILL_TIMEOUT = 600  # 10 min — LLM calls are slow but shouldn't hang forever
        log.info(f"[worker] ▶ {job.skill_name} | {job.account_name} | trigger={job.trigger}")

        try:
            result = await asyncio.wait_for(
                skill.generate(job.account_name),
                timeout=SKILL_TIMEOUT,
            )
            elapsed = round(time.time() - t0, 1)

            if result and result.strip().startswith("❌"):
                log.warning(f"[worker] ✗ {job.skill_name} | {job.account_name} | {elapsed}s | LLM error")
                if self.learner:
                    await self.learner.record(job.account_name, job.skill_name, job.trigger, status="error")
            else:
                log.info(f"[worker] ✓ {job.skill_name} | {job.account_name} | {elapsed}s")

                # Persist output to disk
                output_file = SKILL_OUTPUT_FILES.get(job.skill_name)
                if output_file and result:
                    await skill.write_output(job.account_name, output_file, result)
                    log.info(f"[worker] wrote {output_file} for {job.account_name}")

                # Track for cascade dedup
                self._recent_runs[f"{job.account_name}::{job.skill_name}"] = time.time()

                # 1. Record in evolution log
                if self.learner:
                    await self.learner.record(job.account_name, job.skill_name, job.trigger, status="ok")

                # 2. Feedback loop — extract new intel from output, merge into discovery.md.
                # Safe for all triggers because:
                # - KnowledgeMerger.was_self_written() has 300s cooldown per account
                # - FileWatcher cycle guard checks was_self_written() → suppresses re-trigger
                # Net effect: skills enrich discovery.md once per run cycle, no infinite loop.
                if self.extractor and self.merger and result:
                    asyncio.ensure_future(
                        self._feedback_safe(job.account_name, job.skill_name, result)
                    )

                # 3. Cascade downstream skills (max depth = 1)
                await self._cascade(job)

        except asyncio.TimeoutError:
            elapsed = round(time.time() - t0, 1)
            log.error(f"[worker] ✗ TIMEOUT {job.skill_name} | {job.account_name} | {elapsed}s — killed")

        except Exception as e:
            elapsed = round(time.time() - t0, 1)
            log.error(f"[worker] ✗ {job.skill_name} | {job.account_name} | {elapsed}s | {e}")

        finally:
            await self.queue.done(job)

    async def _feedback_safe(self, account_name: str, skill_name: str, output: str) -> None:
        """Wrapper so fire-and-forget feedback failures are always logged, never silent."""
        try:
            await self._feedback(account_name, skill_name, output)
        except Exception as e:
            log.error(f"[worker] feedback loop crashed ({skill_name}): {e}", exc_info=True)

    async def _feedback(self, account_name: str, skill_name: str, output: str) -> None:
        """
        Extract new intel from skill output and merge into discovery.md.
        Runs async in background — does not block the main queue loop.
        If new intel is found and written, the file watcher will detect
        the discovery.md change and re-trigger the cascade automatically.
        """
        try:
            merged = await self.merger.merge_from_skill_output(
                account_name, skill_name, output, self.extractor
            )
            if merged:
                log.info(f"[worker] feedback loop: new intel from {skill_name} merged into {account_name}/discovery.md")
        except Exception as e:
            log.warning(f"[worker] feedback failed ({skill_name}): {e}")

    async def _cascade(self, completed_job) -> None:
        await self.trigger_cascade(completed_job.account_name, completed_job.skill_name)

    async def trigger_cascade(self, account_name: str, skill_name: str) -> None:
        """
        Public — trigger cascade for a completed skill.
        Call this after a user-triggered skill succeeds.
        """
        cascade = SKILL_CASCADES.get(skill_name)
        if not cascade:
            return

        priority = cascade.get("priority", PRIORITY_LOW)
        for downstream_skill in cascade["skills"]:
            if downstream_skill in SKIP_AUTO_QUEUE:
                continue
            # Dedup: skip if this downstream skill already ran recently for this account
            recent_key = f"{account_name}::{downstream_skill}"
            last_run = self._recent_runs.get(recent_key, 0)
            if time.time() - last_run < self.RECENT_RUN_WINDOW:
                log.info(
                    f"[worker] cascade dedup — {downstream_skill} ran "
                    f"{int(time.time()-last_run)}s ago for {account_name}, skipping"
                )
                continue
            await self.queue.put(
                account_name=account_name,
                skill_name=downstream_skill,
                priority=priority,
                trigger=f"cascade:{skill_name}",
            )
