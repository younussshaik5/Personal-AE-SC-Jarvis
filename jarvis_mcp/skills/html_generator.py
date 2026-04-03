"""HTML Report Generation Skill — parallel sections"""
from jarvis_mcp.skills.base_skill import BaseSkill


class HtmlGeneratorSkill(BaseSkill):
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        base = f"For {account_name}.\n\nACCOUNT DATA:\n{ctx}\n\nUsing ONLY the data above,"

        sections = [
            {
                "name": "Executive Dashboard (HTML)",
                "prompt": f"{base} generate an HTML section with inline CSS for an executive dashboard showing:\n- Deal snapshot: stage, ARR, probability, timeline\n- Stakeholder table\n- MEDDPICC scorecard (RED/AMBER/GREEN badges)\n\nOutput valid HTML with inline styles. Generate ONLY this section.",
                "model_type": "text",
                "max_tokens": 1500,
            },
            {
                "name": "Risk & Action Report (HTML)",
                "prompt": f"{base} generate an HTML section with inline CSS showing:\n- Top risks with severity badges\n- Competitive positioning summary\n- Next actions table with dates and owners\n\nOutput valid HTML with inline styles. Generate ONLY this section.",
                "model_type": "text",
                "max_tokens": 1200,
            },
        ]

        response = await self.parallel_sections(sections)
        return response
