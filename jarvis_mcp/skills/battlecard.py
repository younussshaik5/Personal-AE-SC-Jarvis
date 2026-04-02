"""Competitive Battlecard Skill — parallel sections"""
from jarvis_mcp.skills.base_skill import BaseSkill


class BattlecardSkill(BaseSkill):
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        base = f"For {account_name}.\n\nACCOUNT DATA:\n{ctx}\n\nUsing ONLY the data above,"

        sections = [
            {
                "name": "Competitor Profile & Comparison",
                "prompt": f"{base} write:\n1. Incumbent / primary competitor (from deal data and discovery)\n2. Side-by-side capability comparison: our product vs competitor — use actual features mentioned in discovery\n3. Competitor weaknesses to exploit — based on what the customer complained about\n\nDo NOT invent competitors not in the data. Generate ONLY this section.",
                "max_tokens": 1200,
            },
            {
                "name": "Our Differentiators & Positioning",
                "prompt": f"{base} write:\n1. Our winning differentiators — tied to what the customer said they want\n2. Positioning statement for this specific deal (2 sentences)\n\nGenerate ONLY this section.",
                "max_tokens": 800,
            },
            {
                "name": "Objection Handlers & Killer Questions",
                "prompt": f"{base} write:\n1. Objection handlers — for the specific objections or concerns raised in discovery\n2. Killer questions to ask that expose the competitor's gap without naming them directly\n\nGenerate ONLY this section.",
                "max_tokens": 1000,
            },
        ]

        response = await self.parallel_sections(sections)
        await self.write_output(account_name, "battlecard.md", response)
        return response
