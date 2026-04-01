"""Scope of Work Generation Skill"""
from jarvis_mcp.skills.base_skill import BaseSkill


class SowSkill(BaseSkill):
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        prompt = f"""Write a Statement of Work (SOW) for {account_name}.

ACCOUNT DATA:
{ctx}

Using ONLY the data above, write a professional SOW covering:
1. Project overview — what is being implemented (product, plan, agents from deal data)
2. Scope of work — based on confirmed requirements from discovery
3. Out of scope — explicitly list anything NOT included (prevents scope creep)
4. Deliverables with acceptance criteria
5. Implementation timeline — reverse-engineered from their deadline in deal data
6. Milestones and checkpoints
7. Customer responsibilities (data migration, UAT, stakeholder availability)
8. Commercial terms summary (ARR from deal data)

Reference the actual integration requirements mentioned in discovery (SSO, API integrations, etc.).
Use the customer's actual name and the named stakeholders from deal data.
Do NOT add scope items not grounded in the discovery or deal data."""

        response = await self.llm.generate(
            prompt=prompt,
            model_type="reasoning",
            system_prompt=self.grounded_system_prompt(),
            max_tokens=4000,
        )
        await self.write_output(account_name, "sow.md", response)
        return response
