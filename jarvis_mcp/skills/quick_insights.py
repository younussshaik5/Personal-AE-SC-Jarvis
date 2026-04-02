"""Quick Deal Insights Skill — parallel sections (fast model)"""
from jarvis_mcp.skills.base_skill import BaseSkill


class QuickInsightsSkill(BaseSkill):
    MODEL_TYPE = "fast"
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        base = f"For {account_name}.\n\nACCOUNT DATA:\n{ctx}\n\nUsing ONLY the data above,"

        sections = [
            {
                "name": "Deal Snapshot & Signals",
                "prompt": f"{base} provide:\n1. Deal snapshot: stage, ARR, win prob, forecast date — actual numbers\n2. Top 3 buying signals confirmed so far\n3. Competitive threat: incumbent name, their strength, our counter\n\nBullet points only. No padding. Generate ONLY this section.",
                "model_type": "fast",
                "max_tokens": 600,
            },
            {
                "name": "Risks & Next Action",
                "prompt": f"{base} provide:\n1. Top 3 risks right now (RED items first)\n2. MEDDPICC gaps: dimensions that are RED or missing\n3. #1 next action with a specific date and owner\n\nBullet points only. No padding. Generate ONLY this section.",
                "model_type": "fast",
                "max_tokens": 600,
            },
        ]

        response = await self.parallel_sections(sections)
        await self.write_output(account_name, "quick_insights.md", response)
        return response
