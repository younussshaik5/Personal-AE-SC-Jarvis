#!/usr/bin/env python3
"""
SelfLearner — JARVIS prompt evolution engine.

What this does:
  - Watches every output JARVIS generates (saved in INTEL/ folders)
  - Tracks which outputs you used, edited heavily, or ignored
  - Uses NVIDIA to analyze the diffs (generated vs what you actually sent/used)
  - Identifies patterns: "emails always get shortened" / "proposals need more ROI numbers"
  - Rewrites its own prompt templates based on real feedback
  - Logs every change in MEMORY/evolution_log.md

This is NOT model training. It's prompt evolution.
The system's behavior changes based on what actually works for YOU.

Runs: weekly (Sunday night) + triggered by outcome signals
"""

import asyncio
import difflib
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import Event, EventBus
from jarvis.utils.config import ConfigManager


PROMPT_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "data" / "prompts"
EVOLUTION_LOG = "MEMORY/evolution_log.md"


class SelfLearner:
    """
    Evolves JARVIS prompt templates based on real usage patterns.
    The more you use JARVIS, the more it behaves like you want it to.
    """

    def __init__(self, config_manager: ConfigManager, event_bus: EventBus):
        self.config = config_manager
        self.event_bus = event_bus
        self.logger = JARVISLogger("brain.self_learner")
        self._running = False
        self._weekly_task: Optional[asyncio.Task] = None
        self._llm_client = None

    async def start(self):
        self._running = True
        self._jarvis_home = Path(self.config.workspace_root)
        PROMPT_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        (self._jarvis_home / "MEMORY").mkdir(exist_ok=True)

        # Subscribe to outcome signals
        self.event_bus.subscribe("output.rated", self._on_output_rated)
        self.event_bus.subscribe("output.edited", self._on_output_edited)
        self.event_bus.subscribe("deal.won", self._on_deal_outcome)
        self.event_bus.subscribe("deal.lost", self._on_deal_outcome)

        # Weekly evolution loop
        self._weekly_task = asyncio.create_task(self._weekly_evolution_loop())
        self.logger.info("SelfLearner started")

    async def stop(self):
        self._running = False
        if self._weekly_task and not self._weekly_task.done():
            self._weekly_task.cancel()

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    async def _on_output_rated(self, event: Event):
        """User rated a JARVIS output via jarvis_rate_output MCP tool."""
        self._append_feedback_signal(event.data)

    async def _on_output_edited(self, event: Event):
        """User significantly edited a JARVIS draft before using it."""
        self._append_feedback_signal(event.data)

    async def _on_deal_outcome(self, event: Event):
        """Deal closed won/lost — strong signal for what worked."""
        account = event.data.get("account", "")
        outcome = "won" if event.type == "deal.won" else "lost"
        self.logger.info("Deal outcome recorded", account=account, outcome=outcome)
        # Trigger immediate analysis for this account
        asyncio.create_task(self._analyze_deal_history(account, outcome))

    # ------------------------------------------------------------------
    # Weekly evolution loop
    # ------------------------------------------------------------------

    async def _weekly_evolution_loop(self):
        """Run evolution analysis every Sunday night."""
        while self._running:
            now = datetime.now()
            # Next Sunday at 23:00
            days_until_sunday = (6 - now.weekday()) % 7
            if days_until_sunday == 0 and now.hour >= 23:
                days_until_sunday = 7
            next_run = now.replace(hour=23, minute=0, second=0, microsecond=0) + \
                       timedelta(days=days_until_sunday)
            wait_seconds = (next_run - now).total_seconds()

            self.logger.info("Next evolution run scheduled", next_run=str(next_run))
            await asyncio.sleep(min(wait_seconds, 3600))  # check every hour

            if datetime.now() >= next_run:
                await self.run_evolution_cycle()

    async def run_evolution_cycle(self):
        """
        Full evolution cycle:
        1. Collect all feedback signals from the week
        2. Analyze patterns per skill
        3. Rewrite underperforming prompts
        4. Write evolution log
        """
        self.logger.info("Starting weekly evolution cycle")
        llm = self._get_llm_client()
        if not llm:
            self.logger.warning("No LLM client — skipping evolution")
            return

        signals = self._load_all_feedback_signals()
        if not signals:
            self.logger.info("No feedback signals this week — nothing to evolve")
            return

        # Group signals by skill
        by_skill: Dict[str, List[Dict]] = {}
        for s in signals:
            skill = s.get("skill", "unknown")
            by_skill.setdefault(skill, []).append(s)

        evolution_entries = []

        for skill, skill_signals in by_skill.items():
            result = await self._evolve_skill_prompt(skill, skill_signals, llm)
            if result:
                evolution_entries.append(result)

        # Write evolution log
        if evolution_entries:
            self._write_evolution_log(evolution_entries)
            self.event_bus.publish(Event(
                type="jarvis.evolved",
                source="brain.self_learner",
                data={"skills_evolved": [e["skill"] for e in evolution_entries]}
            ))
            self.logger.info("Evolution cycle complete",
                             skills_evolved=len(evolution_entries))

        # Clear processed signals
        self._clear_feedback_signals()

    # ------------------------------------------------------------------
    # Skill prompt evolution
    # ------------------------------------------------------------------

    async def _evolve_skill_prompt(
        self, skill: str, signals: List[Dict], llm
    ) -> Optional[Dict]:
        """Analyze signals for a skill and rewrite its prompt if needed."""
        current_prompt = self._load_skill_prompt(skill)
        if not current_prompt:
            return None

        # Calculate signal stats
        total = len(signals)
        heavily_edited = sum(1 for s in signals if s.get("heavily_edited", False))
        unused = sum(1 for s in signals if not s.get("used", True))
        poor_ratings = sum(1 for s in signals if s.get("rating", 3) <= 2)

        edit_rate = heavily_edited / total if total > 0 else 0
        unused_rate = unused / total if total > 0 else 0

        # Only evolve if there's a real problem
        if edit_rate < 0.3 and unused_rate < 0.3 and poor_ratings < 2:
            return None  # Performing fine — don't touch it

        # Collect edit examples for NVIDIA to learn from
        edit_examples = [
            {"generated": s.get("generated", ""), "final": s.get("final", "")}
            for s in signals
            if s.get("heavily_edited") and s.get("generated") and s.get("final")
        ][:5]  # max 5 examples

        prompt = f"""You are improving a prompt template for an AI sales assistant.

CURRENT PROMPT for skill "{skill}":
{current_prompt[:2000]}

USAGE SIGNALS this week:
- Total outputs generated: {total}
- Heavily edited by user: {heavily_edited} ({edit_rate:.0%})
- Ignored/unused: {unused} ({unused_rate:.0%})
- Poor ratings (≤2/5): {poor_ratings}

EDIT EXAMPLES (what user changed):
{json.dumps(edit_examples, indent=2)[:3000]}

TASK:
1. Identify exactly WHY the user is editing these outputs
2. Rewrite the prompt to produce outputs closer to what the user wants
3. Keep the same structure and variables — only change the instructions

Return JSON:
{{
  "diagnosis": "Why outputs needed editing",
  "changes_made": "What you changed in the prompt and why",
  "new_prompt": "The full rewritten prompt"
}}"""

        try:
            response = await llm.generate_with_routing(
                messages=[{"role": "user", "content": prompt}],
                task_type="text",
                source="background",
            )
            parsed = self._extract_json(response)
            if parsed and parsed.get("new_prompt"):
                # Save evolved prompt
                self._save_skill_prompt(skill, parsed["new_prompt"])
                return {
                    "skill": skill,
                    "timestamp": datetime.now().isoformat(),
                    "signals_analyzed": total,
                    "diagnosis": parsed.get("diagnosis", ""),
                    "changes": parsed.get("changes_made", ""),
                }
        except Exception as e:
            self.logger.error("Prompt evolution failed", skill=skill, error=str(e))

        return None

    async def _analyze_deal_history(self, account: str, outcome: str):
        """When a deal closes, analyze what worked or didn't and feed back."""
        llm = self._get_llm_client()
        if not llm:
            return

        account_dir = self._jarvis_home / "ACCOUNTS" / account
        if not account_dir.exists():
            return

        # Collect everything JARVIS generated for this deal
        intel_files = list((account_dir / "INTEL").glob("*.md")) if \
            (account_dir / "INTEL").exists() else []
        activities = self._read_activities(account_dir)
        meddpicc = self._read_json(account_dir / "meddpicc.json")

        context = {
            "account": account,
            "outcome": outcome,
            "final_meddpicc_score": meddpicc.get("score", 0) if meddpicc else 0,
            "intel_files_count": len(intel_files),
            "activities_count": len(activities),
            "stage_history": self._read_json(account_dir / "deal_stage.json"),
        }

        prompt = f"""A sales deal just closed {outcome.upper()}.

Deal summary:
{json.dumps(context, indent=2)}

Based on this outcome, identify:
1. What signals predicted this outcome (that JARVIS should weight more heavily)?
2. What was missing from JARVIS's analysis that would have helped?
3. What playbook actions were most/least useful?
4. One specific recommendation to improve JARVIS for similar deals.

Return JSON: {{"signals": [], "gaps": [], "recommendations": []}}"""

        try:
            response = await llm.generate_with_routing(
                [{"role": "user", "content": prompt}],
                task_type="text",
                source="background",
            )
            parsed = self._extract_json(response)
            if parsed:
                # Write learning to MEMORY
                learning_file = self._jarvis_home / "MEMORY" / \
                    f"deal_learning_{account.replace(' ', '_')}_{outcome}.json"
                learning_file.write_text(json.dumps({
                    "account": account,
                    "outcome": outcome,
                    "timestamp": datetime.now().isoformat(),
                    **parsed
                }, indent=2))
                self.logger.info("Deal learning recorded", account=account, outcome=outcome)
        except Exception as e:
            self.logger.error("Deal analysis failed", account=account, error=str(e))

    # ------------------------------------------------------------------
    # Prompt storage
    # ------------------------------------------------------------------

    def _load_skill_prompt(self, skill: str) -> Optional[str]:
        prompt_file = PROMPT_TEMPLATES_DIR / f"{skill}.md"
        if prompt_file.exists():
            return prompt_file.read_text(encoding="utf-8")
        # Try to extract from skill Python file
        skill_py = Path(__file__).resolve().parent.parent / "skills" / f"{skill}_skill.py"
        if skill_py.exists():
            content = skill_py.read_text()
            match = re.search(r'prompt\s*=\s*f?"""(.*?)"""', content, re.DOTALL)
            if match:
                return match.group(1)
        return None

    def _save_skill_prompt(self, skill: str, prompt: str):
        PROMPT_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        prompt_file = PROMPT_TEMPLATES_DIR / f"{skill}.md"
        # Backup current version
        if prompt_file.exists():
            backup = PROMPT_TEMPLATES_DIR / f"{skill}_backup_{datetime.now().strftime('%Y%m%d')}.md"
            backup.write_text(prompt_file.read_text())
        prompt_file.write_text(prompt, encoding="utf-8")
        self.logger.info("Skill prompt evolved", skill=skill)

    # ------------------------------------------------------------------
    # Feedback signal storage
    # ------------------------------------------------------------------

    def _feedback_file(self) -> Path:
        return self._jarvis_home / "data" / "feedback_signals.jsonl"

    def _append_feedback_signal(self, data: Dict):
        f = self._feedback_file()
        f.parent.mkdir(parents=True, exist_ok=True)
        with open(f, "a") as fp:
            fp.write(json.dumps({**data, "timestamp": datetime.now().isoformat()}) + "\n")

    def _load_all_feedback_signals(self) -> List[Dict]:
        f = self._feedback_file()
        if not f.exists():
            return []
        signals = []
        for line in f.read_text().splitlines():
            try:
                signals.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        return signals

    def _clear_feedback_signals(self):
        f = self._feedback_file()
        archive = f.parent / f"feedback_signals_archive_{datetime.now().strftime('%Y%m%d')}.jsonl"
        if f.exists():
            f.rename(archive)

    # ------------------------------------------------------------------
    # Evolution log
    # ------------------------------------------------------------------

    def _write_evolution_log(self, entries: List[Dict]):
        log_file = self._jarvis_home / EVOLUTION_LOG
        log_file.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"\n## Evolution Cycle — {datetime.now().strftime('%Y-%m-%d')}\n"]
        for entry in entries:
            lines.append(f"### Skill: `{entry['skill']}`")
            lines.append(f"- Signals analyzed: {entry['signals_analyzed']}")
            lines.append(f"- Diagnosis: {entry['diagnosis']}")
            lines.append(f"- Changes: {entry['changes']}\n")
        with open(log_file, "a") as f:
            f.write("\n".join(lines))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_llm_client(self):
        if not self._llm_client:
            try:
                from jarvis.llm.llm_client import LLMClient
                self._llm_client = LLMClient(self.config)
            except Exception:
                pass
        return self._llm_client

    def _extract_json(self, text: str) -> Optional[Dict]:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return None

    def _read_json(self, path: Path) -> Optional[Dict]:
        try:
            return json.loads(path.read_text()) if path.exists() else None
        except Exception:
            return None

    def _read_activities(self, account_dir: Path) -> List[Dict]:
        f = account_dir / "activities.jsonl"
        if not f.exists():
            return []
        result = []
        for line in f.read_text().splitlines()[-50:]:  # last 50
            try:
                result.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        return result
