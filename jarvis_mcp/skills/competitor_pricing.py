"""Competitor Pricing Analysis Skill — parallel sections"""
from jarvis_mcp.skills.base_skill import BaseSkill


class CompetitorPricingSkill(BaseSkill):
    MODEL_TYPE = "reasoning"
    async def generate(self, account_name: str, competitor: str = "", **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)
        comp = competitor or (context.get("_deal", {}) or {}).get("competitive_situation", {}).get("primary_competitor", "the incumbent")

        base = f"For {account_name} vs {comp}.\n\nACCOUNT DATA:\n{ctx}\n\nUsing ONLY the data above plus general knowledge of {comp}'s public pricing model,"

        sections = [
            {
                "name": "Pricing Comparison",
                "prompt": f"{base} write:\n1. Our pricing for this deal: actual ARR, per-agent cost, plan from deal data\n2. Estimated competitor pricing (use public knowledge for {comp} — clearly label as estimate)\n3. TCO comparison over 1 year and 3 years\n\nClearly separate facts from account data vs general market knowledge. Generate ONLY this section.",
                "max_tokens": 1000,
            },
            {
                "name": "Price Positioning & Strategy",
                "prompt": f"{base} write:\n1. Where we are more expensive and how to justify it\n2. Where we are cheaper — use this proactively\n3. Discount strategy: what to offer and when (tied to their deadline from deal data)\n\nGenerate ONLY this section.",
                "max_tokens": 800,
            },
            {
                "name": "Commercial Objection Handlers",
                "prompt": f"{base} write commercial objection handlers specific to this deal and {comp}. Address pricing objections grounded in the account data.\n\nGenerate ONLY this section.",
                "max_tokens": 600,
            },
        ]

        response = await self.parallel_sections(sections)
        await self.write_output(account_name, "competitor_pricing.md", response)
        return response
