"""ROI and Value Architecture Skill"""
from jarvis_mcp.skills.base_skill import BaseSkill


class ValueArchitectureSkill(BaseSkill):
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        prompt = f"""Build a value architecture and ROI model for {account_name}.

ACCOUNT DATA:
{ctx}

Using ONLY the data above, build a grounded value case:

1. Business problems being solved (from discovery — use actual pain points mentioned)
2. Quantified value per problem area where numbers exist in the data
3. ROI model using actual inputs (agents count, ARR, deal size from deal data):
   - Conservative / Realistic / Optimistic scenarios
   - Payback period calculation
   - Year 1 ROI %
4. TCO comparison: current state cost (incumbent + in-house) vs our solution
5. Value statement: 2-sentence executive summary for the economic buyer

Where numbers are not in the data, say "To be quantified in discovery" — do NOT invent metrics."""

        response = await self.llm.generate(
            prompt=prompt,
            model_type="reasoning",
            system_prompt=self.grounded_system_prompt(),
            max_tokens=3000,
        )
        await self.write_output(account_name, "value_architecture.md", response)
        return response
