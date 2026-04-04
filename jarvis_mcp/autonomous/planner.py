"""
Autonomous planner — decides which retry strategy to use next,
and generates human-readable todo explanations via step-3.5-flash.
"""

import logging
from typing import List, Optional

log = logging.getLogger(__name__)

# ── Strategy constants ────────────────────────────────────────────────────────

STRATEGY_DEFAULT        = "default"
STRATEGY_WRITING_MODEL  = "writing_model"
STRATEGY_REASONING_MODEL = "reasoning_model"
STRATEGY_TODO           = "todo"

# Order of escalation — first strategy not yet tried is selected
STRATEGY_ESCALATION: List[str] = [
    STRATEGY_DEFAULT,
    STRATEGY_WRITING_MODEL,
    STRATEGY_REASONING_MODEL,
    STRATEGY_TODO,
]

# Maps strategy → model_type override for LLMManager (None = use skill's default)
STRATEGY_MODEL_MAP = {
    STRATEGY_DEFAULT:         None,
    STRATEGY_WRITING_MODEL:   "writing",
    STRATEGY_REASONING_MODEL: "reasoning",
    STRATEGY_TODO:            None,
}


class AutonomousPlanner:
    """
    Decision maker for autonomous retry logic.

    Uses step-3.5-flash (model_type="autonomous") only for todo explanations.
    All other decisions are purely deterministic.
    """

    def __init__(self, llm_manager):
        self.llm = llm_manager

    def next_strategy(self, failure_reason: str, strategies_tried: List[str]) -> str:
        """
        Return the next strategy to try from STRATEGY_ESCALATION
        that has not been tried yet.
        Falls back to STRATEGY_TODO if all have been tried.
        """
        for strategy in STRATEGY_ESCALATION:
            if strategy not in strategies_tried:
                return strategy
        return STRATEGY_TODO

    def model_override(self, strategy: str) -> Optional[str]:
        """Return the model_type override for this strategy, or None."""
        return STRATEGY_MODEL_MAP.get(strategy)

    async def explain_todo(
        self,
        account: str,
        skill: str,
        failure_reason: str,
        strategies_tried: List[str],
        context_summary: str,
    ) -> str:
        """
        Call LLM (step-3.5-flash via model_type="autonomous") to produce a
        one-sentence root cause + recommended human action.

        Falls back to a static string if the LLM call fails.
        Only the first sentence is returned.
        """
        prompt = (
            f"JARVIS skill '{skill}' failed for account '{account}' after trying strategies: "
            f"{', '.join(strategies_tried)}.\n"
            f"Last failure: {failure_reason}\n"
            f"Deal context: {context_summary}\n\n"
            "In one sentence, state the root cause and what a human should do to resolve this."
        )

        try:
            explanation = await self.llm.generate(
                prompt=prompt,
                model_type="autonomous",
                max_tokens=120,
            )
            if explanation:
                # Strip to first sentence only
                first_sentence = explanation.strip().split(".")[0].strip()
                if first_sentence:
                    return first_sentence + "."
        except Exception as e:
            log.warning(f"[planner] explain_todo LLM call failed: {e}")

        # Static fallback
        return (
            f"Skill '{skill}' for '{account}' failed all retry strategies "
            f"({', '.join(strategies_tried)}) — manual review required."
        )
