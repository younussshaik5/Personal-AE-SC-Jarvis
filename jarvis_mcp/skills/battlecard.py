"""Competitive Battlecard Skill"""
from jarvis_mcp.skills.base_skill import BaseSkill


class BattlecardSkill(BaseSkill):
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        prompt = f"""Generate a competitive battlecard for {account_name}.

ACCOUNT DATA:
{ctx}

Using ONLY the data above, build a battlecard covering:
1. Incumbent / primary competitor (from deal data and discovery)
2. Side-by-side capability comparison: our product vs competitor — use actual features mentioned in discovery
3. Competitor weaknesses to exploit — based on what the customer complained about
4. Our winning differentiators — tied to what the customer said they want
5. Objection handlers — for the specific objections or concerns raised in discovery
6. Killer questions to ask that expose the competitor's gap
7. Positioning statement for this specific deal (2 sentences)

Do NOT invent competitors, features, or objections not mentioned in the data."""

        response = await self.llm.generate(
            prompt=prompt,
            model_type="reasoning",
            system_prompt=self.grounded_system_prompt(),
            max_tokens=3000,
        )
        await self.write_output(account_name, "battlecard.md", response)
        return response
