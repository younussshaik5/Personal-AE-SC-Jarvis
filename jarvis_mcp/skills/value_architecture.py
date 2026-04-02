"""ROI and Value Architecture Skill — parallel sections"""
from jarvis_mcp.skills.base_skill import BaseSkill


class ValueArchitectureSkill(BaseSkill):
    MODEL_TYPE = "reasoning"
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        base = f"For {account_name}.\n\nACCOUNT DATA:\n{ctx}\n\nUsing ONLY the data above,"

        sections = [
            {
                "name": "Business Problems & Quantified Value",
                "prompt": f"{base} write:\n1. Business problems being solved (from discovery — use actual pain points)\n2. Quantified value per problem area where numbers exist in the data\n\nWhere numbers are not in the data, say 'To be quantified in discovery'. Generate ONLY this section.",
                "max_tokens": 1000,
            },
            {
                "name": "ROI Model & TCO Comparison",
                "prompt": f"{base} build:\n1. ROI model using actual inputs (agents count, ARR, deal size from deal data):\n   - Conservative / Realistic / Optimistic scenarios\n   - Payback period calculation\n   - Year 1 ROI %\n2. TCO comparison: current state cost (incumbent + in-house) vs our solution\n\nUse actual numbers from the data. Where numbers are missing say 'To be quantified'. Generate ONLY this section.",
                "max_tokens": 1200,
            },
            {
                "name": "Executive Value Statement",
                "prompt": f"{base} write a 2-sentence executive value summary for the economic buyer, grounded in the actual deal data and pain points. Generate ONLY this section.",
                "max_tokens": 400,
            },
        ]

        response = await self.parallel_sections(sections)
        await self.write_output(account_name, "value_architecture.md", response)
        return response
