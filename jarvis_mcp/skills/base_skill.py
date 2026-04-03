"""BaseSkill - All skills inherit from this"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from jarvis_mcp.utils.file_utils import read_file, write_file


class BaseSkill:
    """Base class for all skills"""

    # Override in subclasses to route to the right model profile.
    # reasoning → deep analysis (MEDDPICC, risk, competitive)
    # writing   → long-form generation (proposals, SOW, battlecards)
    # fast      → quick tasks (summaries, insights, follow-ups)
    # default   → general purpose
    MODEL_TYPE: str = "default"

    def __init__(self, llm_manager, config_manager):
        self.llm = llm_manager
        self.config = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)

    async def execute(self, arguments: Dict[str, Any]) -> str:
        account_name = arguments.get("account_name", "")
        if not account_name:
            return "❌ account_name is required."
        extra = {k: v for k, v in arguments.items() if k != "account_name"}
        try:
            result = await self.generate(account_name, **extra)
            return result or "✅ Done."
        except Exception as e:
            self.logger.error(f"execute() failed: {e}", exc_info=True)
            return f"❌ Error: {e}"

    async def read_account_files(self, account_name: str) -> Dict[str, str]:
        """Read all account files — .md files + deal_stage.json."""
        account_path = self.config.get_account_path(account_name)
        if not account_path.exists():
            self.logger.warning(f"Account path doesn't exist: {account_path}")
            return {}

        context = {}

        # Read all .md files (including _evolution_log.md)
        for md_file in sorted(account_path.glob("*.md")):
            key = md_file.stem
            content = await read_file(md_file)
            if content and content.strip():
                context[key] = content

        # Read deal_stage.json and parse into a readable string
        ds_file = account_path / "deal_stage.json"
        if ds_file.exists():
            try:
                ds_text = await read_file(ds_file)
                ds = json.loads(ds_text)
                context["_deal"] = ds  # raw dict for structured access
                # Also build a human-readable summary
                lines = [
                    f"Account: {ds.get('account_name', account_name)}",
                    f"Stage: {ds.get('stage', 'Unknown')}",
                    f"Deal Size / ARR: ${ds.get('deal_size', ds.get('arr', 0)):,}",
                    f"Win Probability: {int(ds.get('probability', 0) * 100)}%",
                    f"Timeline / Forecast: {ds.get('timeline', ds.get('forecast_date', 'TBD'))}",
                    f"Product: {ds.get('product', 'TBD')}",
                    f"Agents: {ds.get('num_agents', 'TBD')}",
                ]
                # Stakeholders
                for s in ds.get("stakeholders", []):
                    if isinstance(s, dict):
                        lines.append(f"Stakeholder: {s.get('name','?')} — {s.get('title','?')} ({s.get('role','?')}) | {s.get('notes','')}")
                    else:
                        lines.append(f"Stakeholder: {s}")
                # Competitive
                comp = ds.get("competitive_situation", {})
                if comp:
                    lines.append(f"Primary Competitor: {comp.get('primary_competitor','TBD')} — {comp.get('competitor_status','')}")
                # Constraints
                for c in ds.get("constraints", []):
                    lines.append(f"Constraint: {c}")
                # Activities
                for a in ds.get("activities", [])[-5:]:  # last 5
                    if isinstance(a, dict):
                        lines.append(f"Activity [{a.get('date','')}]: {a.get('type','')} — {a.get('notes','')}")
                # Next milestone
                nm = ds.get("next_milestone", {})
                if nm:
                    lines.append(f"Next Milestone: {nm.get('activity','?')} by {nm.get('date','?')} — {nm.get('description','')}")
                context["deal_stage"] = "\n".join(lines)
            except Exception as e:
                self.logger.warning(f"Could not parse deal_stage.json: {e}")

        return context

    def build_context_block(self, context: Dict[str, Any], account_name: str) -> str:
        """Build a rich, grounded context block for LLM prompts."""
        parts = []

        ds = context.get("deal_stage", "")
        if ds:
            parts.append(f"=== DEAL DATA ===\n{ds}")

        cr = context.get("company_research", "")
        if cr:
            parts.append(f"=== COMPANY RESEARCH ===\n{cr[:6000]}")

        disc = context.get("discovery", "")
        if disc:
            # Use TAIL of file — real intel is appended at the bottom;
            # the top is the blank MEDDPICC template (~4000 chars of TBDs)
            DISC_LIMIT = 14000
            disc_content = disc[-DISC_LIMIT:] if len(disc) > DISC_LIMIT else disc
            parts.append(f"=== DISCOVERY NOTES ===\n{disc_content}")

        # Evolution log — what skills ran recently and what they found
        evo = context.get("_evolution_log", "")
        if evo:
            # Only include the last 30 lines — enough for context, not noisy
            lines = [l for l in evo.splitlines() if l.strip() and not l.startswith("#")]
            recent = "\n".join(lines[-30:])
            if recent:
                parts.append(f"=== RECENT EVOLUTION LOG ===\n{recent}")

        # Include any other skill outputs already generated
        skip = {"deal_stage", "company_research", "discovery", "CLAUDE", "_deal",
                "_evolution_log", "_skill_timeline"}
        for key, val in context.items():
            if key not in skip and isinstance(val, str) and val.strip():
                parts.append(f"=== {key.upper().replace('_', ' ')} ===\n{val[:3000]}")

        if not parts:
            return f"Account: {account_name}\n(No account data found — run discovery first)"

        return "\n\n".join(parts)

    def grounded_system_prompt(self) -> str:
        """System prompt that forces grounded, file-based generation."""
        return (
            "You are JARVIS, an expert AI sales assistant. "
            "CRITICAL RULE: Generate output ONLY from the account data provided below. "
            "Do NOT invent facts, names, titles, competitors, metrics, or timelines. "
            "If a field is missing from the data, say 'TBD — needs discovery' rather than guessing. "
            "Every claim must be traceable to the provided context. "
            "MANDATORY: Every section MUST contain substantive content. "
            "A blank or empty section is NEVER acceptable — if data is missing, "
            "state what is missing, why it matters, and the specific discovery question that would fill the gap. "
            "Do NOT repeat the section heading at the start of your response. "
            "Output professional markdown."
        )

    async def write_output(self, account_name: str, filename: str, content: str) -> bool:
        # Never overwrite a good file with an error message
        if content and content.strip().startswith("❌"):
            self.logger.error(f"Skipping write of {filename} — LLM returned error: {content[:100]}")
            return False
        try:
            account_path = self.config.get_account_path(account_name)
            account_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            self.logger.error(f"Cannot create account path for {account_name}: {e}")
            return False
        output_path = account_path / filename
        try:
            success = await write_file(output_path, content)
            if success:
                self.logger.info(f"Wrote {filename} for {account_name}")
            else:
                self.logger.error(f"write_file returned False for {filename} ({account_name})")
            return success
        except Exception as e:
            self.logger.error(f"Unexpected error writing {filename} for {account_name}: {e}")
            return False

    async def parallel_sections(self, sections: List[Dict[str, Any]]) -> str:
        """
        Fire multiple section prompts in parallel via asyncio.gather.

        sections: list of dicts, each with:
            - name: section heading
            - prompt: full prompt including account context
            - model_type (optional): defaults to "reasoning"
            - max_tokens (optional): defaults to 1000
        Returns: assembled markdown string with all sections.
        """
        async def _gen(section):
            return await self.llm.generate(
                prompt=section["prompt"],
                model_type=section.get("model_type", self.MODEL_TYPE),
                system_prompt=self.grounded_system_prompt(),
                max_tokens=section.get("max_tokens", 1000),
            )

        tasks = [asyncio.ensure_future(_gen(s)) for s in sections]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        import re
        parts = []
        for section, result in zip(sections, results):
            if isinstance(result, Exception):
                parts.append(f"## {section['name']}\n\n❌ Generation failed: {result}")
            else:
                # Strip any leading heading the LLM duplicated (prevents double ## headers)
                name_escaped = re.escape(section["name"])
                cleaned = re.sub(
                    rf"^#+\s+{name_escaped}\s*\n*", "", result.strip(),
                    count=1, flags=re.IGNORECASE
                ).strip()
                parts.append(f"## {section['name']}\n\n{cleaned}")

        return "\n\n---\n\n".join(parts)

    async def generate(self, account_name: str, **kwargs) -> str:
        raise NotImplementedError()
