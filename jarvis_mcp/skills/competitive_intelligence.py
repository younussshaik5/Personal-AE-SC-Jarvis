"""Competitive Intelligence Skill"""
from jarvis_mcp.skills.base_skill import BaseSkill


class CompetitiveIntelligenceSkill(BaseSkill):
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        prompt = f"""Build competitive intelligence for {account_name}.

ACCOUNT DATA:
{ctx}

Using ONLY the data above, analyse the competitive situation:
1. Confirmed competitor(s): names and roles (incumbent, shortlisted, etc.) from deal data
2. Why the customer is evaluating alternatives — their stated reason from discovery
3. Competitor's likely strengths in this account (based on why they're incumbent or chosen)
4. Competitor's weaknesses tied to what this customer wants
5. Our differentiated position for THIS customer's specific requirements
6. Counter-positioning: how to reframe the evaluation criteria in our favour
7. Questions to ask that expose the competitor's gap without naming them
8. Risk: could the customer stay with the incumbent? What would cause that?

If only one competitor is in the data, focus only on that one. Do NOT add competitors not mentioned in the data."""

        response = await self.llm.generate(
            prompt=prompt,
            model_type="reasoning",
            system_prompt=self.grounded_system_prompt(),
            max_tokens=2500,
        )
        await self.write_output(account_name, "competitive_intelligence.md", response)
        return response
