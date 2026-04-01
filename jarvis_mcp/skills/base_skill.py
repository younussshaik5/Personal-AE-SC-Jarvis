"""BaseSkill - All skills inherit from this"""

import json
import logging
from pathlib import Path
from typing import Dict, Any
from jarvis_mcp.utils.file_utils import read_file, write_file


class BaseSkill:
    """Base class for all skills"""

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

        # Read all .md files
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
            parts.append(f"=== COMPANY RESEARCH ===\n{cr[:4000]}")

        disc = context.get("discovery", "")
        if disc:
            parts.append(f"=== DISCOVERY NOTES ===\n{disc[:5000]}")

        # Include any other skill outputs already generated
        skip = {"deal_stage", "company_research", "discovery", "CLAUDE", "_deal"}
        for key, val in context.items():
            if key not in skip and isinstance(val, str) and val.strip():
                parts.append(f"=== {key.upper().replace('_', ' ')} ===\n{val[:2000]}")

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
            "Output professional markdown."
        )

    async def write_output(self, account_name: str, filename: str, content: str) -> bool:
        # Never overwrite a good file with an error message
        if content and content.strip().startswith("❌"):
            self.logger.error(f"Skipping write of {filename} — LLM returned error: {content[:100]}")
            return False
        account_path = self.config.get_account_path(account_name)
        account_path.mkdir(parents=True, exist_ok=True)
        output_path = account_path / filename
        success = await write_file(output_path, content)
        if success:
            self.logger.info(f"Wrote {filename} for {account_name}")
        return success

    async def generate(self, account_name: str, **kwargs) -> str:
        raise NotImplementedError()
