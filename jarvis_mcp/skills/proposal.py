"""Generate Sales Proposals Skill"""
from jarvis_mcp.skills.base_skill import BaseSkill


class ProposalSkill(BaseSkill):
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        prompt = f"""Write a sales proposal for {account_name}.

ACCOUNT DATA:
{ctx}

Using ONLY the data above, write a professional proposal covering:
1. Executive summary — their situation and why they're evaluating (from discovery)
2. Their stated requirements — use the actual list from discovery
3. Our solution — map each requirement to a specific capability
4. Pricing — use the ARR and agent count from deal data
5. Implementation timeline — tied to their deadline from deal data
6. Why us vs the incumbent — use actual competitor from deal data
7. Next steps — specific, dated actions

Address the proposal to the stakeholders named in the data. Reference their actual pain points. Do NOT use placeholder names or invented requirements."""

        response = await self.llm.generate(
            prompt=prompt,
            model_type="reasoning",
            system_prompt=self.grounded_system_prompt(),
            max_tokens=4000,
        )
        await self.write_output(account_name, "proposal.md", response)
        return response
