"""Technical Risk Assessment Skill"""
from jarvis_mcp.skills.base_skill import BaseSkill


class TechnicalRiskSkill(BaseSkill):
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        prompt = f"""Assess technical risks for {account_name}.

ACCOUNT DATA:
{ctx}

Using ONLY the data above, identify technical risks specific to this deal. For each risk:
- Risk: specific technical challenge (e.g. SSO integration, API complexity, data migration)
- Severity: RED / AMBER / GREEN
- Evidence: what in the data signals this risk (integration requirement, legacy system, etc.)
- Pre-sales action: what to validate or demo before close
- Resolution path: how to mitigate or de-risk

Focus on:
- Integration requirements mentioned in discovery
- Legacy/incumbent system dependencies
- Security or compliance requirements (SSO, auth, data residency)
- Any technical unknowns or gaps in discovery

Do NOT invent technical risks not grounded in the account data."""

        response = await self.llm.generate(
            prompt=prompt,
            model_type="reasoning",
            system_prompt=self.grounded_system_prompt(),
            max_tokens=2500,
        )
        await self.write_output(account_name, "technical_risk.md", response)
        return response
