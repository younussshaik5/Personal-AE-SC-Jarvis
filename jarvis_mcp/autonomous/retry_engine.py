"""
Autonomous retry orchestrator for JARVIS.

Wraps every skill execution with multi-strategy retry logic:
  1. Default (skill's own model)
  2. Writing model override
  3. Reasoning model override
  4. Todo — create a human-action todo and return None

Outcomes are persisted to AutonomousMemory so patterns accumulate
across server restarts.
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Optional, List

from .memory import AutonomousMemory
from .validator import validate_output
from .planner import AutonomousPlanner, STRATEGY_DEFAULT, STRATEGY_TODO

log = logging.getLogger(__name__)

MAX_ATTEMPTS = 3


class RetryEngine:
    """
    Main retry orchestrator.

    Usage (from QueueWorker):
        result = await retry_engine.execute_with_retry(skill, account_name, skill_name)
        if result is not None:
            await skill.write_output(account_name, output_file, result)
    """

    def __init__(self, llm_manager, config_manager, memory: AutonomousMemory):
        self.llm     = llm_manager
        self.config  = config_manager
        self.memory  = memory
        self.planner = AutonomousPlanner(llm_manager)

    # ── Public entry point ────────────────────────────────────────────────────

    async def execute_with_retry(
        self,
        skill,
        account_name: str,
        skill_name: str,
    ) -> Optional[str]:
        """
        Execute skill with up to MAX_ATTEMPTS, escalating strategies.
        Returns content string on success/partial, None if todo was created.
        """
        strategies_tried: List[str] = []
        last_failure: str = "no previous attempt"

        for attempt in range(1, MAX_ATTEMPTS + 1):
            # ── Choose strategy ───────────────────────────────────────────────
            if attempt == 1:
                strategy = STRATEGY_DEFAULT
            else:
                strategy = self.planner.next_strategy(last_failure, strategies_tried)

            if strategy == STRATEGY_TODO:
                await self._create_todo(account_name, skill_name, last_failure, strategies_tried)
                return None

            model_override = self.planner.model_override(strategy)

            log.info(
                f"[retry] attempt {attempt}/{MAX_ATTEMPTS} | {skill_name} | {account_name} "
                f"| strategy={strategy} | model_override={model_override}"
            )

            # ── Execute ───────────────────────────────────────────────────────
            t0 = time.time()
            error_type = None
            try:
                content = await self._run_skill(skill, account_name, model_override)
            except asyncio.TimeoutError as e:
                error_type = "timeout"
                log.error(f"[retry] Skill timeout: {skill_name}", exc_info=True)
                content = f"❌ Timeout: Skill execution exceeded time limit"
            except Exception as e:
                error_type = type(e).__name__
                log.error(f"[retry] Skill execution failed ({error_type}): {skill_name}", exc_info=True)
                content = f"❌ {error_type}: {e}"

            elapsed = round(time.time() - t0, 1)

            # ── Validate ──────────────────────────────────────────────────────
            v = validate_output(content, account_name, skill_name)
            verdict = v["verdict"]
            quality = v["quality"]
            reason  = v["reason"]

            log.info(
                f"[retry] verdict={verdict} quality={quality} error_type={error_type} elapsed={elapsed}s | {reason}"
            )

            # ── Record ────────────────────────────────────────────────────────
            error_str = content if verdict == "error" else ""
            self.memory.record_attempt(
                account=account_name,
                skill=skill_name,
                outcome=verdict,
                strategy=strategy,
                quality=quality,
                error=error_str,
            )

            strategies_tried.append(strategy)
            last_failure = f"{verdict}: {reason}"

            # ── Accept good/partial ───────────────────────────────────────────
            if verdict in ("good", "partial"):
                self.memory.resolve_todo(account_name, skill_name)
                return content

        # All attempts exhausted
        await self._create_todo(account_name, skill_name, last_failure, strategies_tried)
        return None

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _run_skill(self, skill, account_name: str, model_override: Optional[str]) -> str:
        """Execute skill, temporarily overriding MODEL_TYPE if specified."""
        original_model_type = getattr(skill, "MODEL_TYPE", None)
        try:
            if model_override:
                skill.MODEL_TYPE = model_override
            return await skill.execute({"account_name": account_name})
        finally:
            if model_override and original_model_type is not None:
                skill.MODEL_TYPE = original_model_type
            elif model_override and original_model_type is None:
                # Attribute didn't exist before — remove it
                try:
                    delattr(skill, "MODEL_TYPE")
                except AttributeError:
                    pass

    async def _create_todo(
        self,
        account: str,
        skill: str,
        failure_reason: str,
        strategies_tried: List[str],
    ) -> None:
        """Build a human-readable todo and persist it to memory."""
        context_summary = self._context_summary(account)
        reason = await self.planner.explain_todo(
            account=account,
            skill=skill,
            failure_reason=failure_reason,
            strategies_tried=strategies_tried,
            context_summary=context_summary,
        )
        todo_id = self.memory.add_todo(account, skill, reason, strategies_tried)
        log.info(
            f"[retry] todo created | id={todo_id} | {skill} | {account} | {reason}"
        )

    def _context_summary(self, account_name: str) -> str:
        """
        Read deal_stage.json for the account and return a compact summary.
        Falls back to "unavailable" if the file is missing or malformed.
        """
        try:
            accounts_root = Path(self.config.accounts_root)
            deal_stage_path = accounts_root / account_name / "deal_stage.json"
            if not deal_stage_path.exists():
                return "unavailable"
            with open(deal_stage_path, "r") as f:
                data = json.load(f)

            stage        = data.get("stage", "unknown")
            arr          = data.get("arr", data.get("ARR", "unknown"))
            competitor   = data.get("competitor", data.get("competition", "unknown"))
            stakeholders = data.get("stakeholders", [])
            if isinstance(stakeholders, list):
                stakeholders = ", ".join(str(s) for s in stakeholders[:3])

            return f"Stage={stage} | ARR={arr} | Competitor={competitor} | Stakeholders={stakeholders}"
        except Exception as e:
            log.debug(f"[retry] _context_summary failed for {account_name}: {e}")
            return "unavailable"
