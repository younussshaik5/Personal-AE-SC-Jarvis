"""Competitor Pricing Analysis Skill"""
from jarvis_mcp.skills.base_skill import BaseSkill


class CompetitorPricingSkill(BaseSkill):
    async def generate(self, account_name: str, competitor: str = "", **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)
        comp = competitor or (context.get("_deal", {}) or {}).get("competitive_situation", {}).get("primary_competitor", "the incumbent")

        prompt = f"""Analyse pricing and commercial positioning for {account_name} vs {comp}.

ACCOUNT DATA:
{ctx}

Using ONLY the data above plus general knowledge of {comp}'s public pricing model:
1. Our pricing for this deal: actual ARR, per-agent cost, plan from deal data
2. Estimated competitor pricing (use public knowledge for {comp} — clearly label as estimate)
3. TCO comparison over 1 year and 3 years
4. Where we are more expensive and how to justify it
5. Where we are cheaper — use this proactively
6. Discount strategy: what to offer and when (tied to their deadline from deal data)
7. Commercial objection handlers for this deal

Clearly separate facts from the account data vs general market knowledge."""

        response = await self.llm.generate(
            prompt=prompt,
            model_type="reasoning",
            system_prompt=self.grounded_system_prompt(),
            max_tokens=2500,
        )
        await self.write_output(account_name, "competitor_pricing.md", response)
        return response
