"""Technical Risk Assessment Skill — parallel sections"""
from jarvis_mcp.skills.base_skill import BaseSkill


class TechnicalRiskSkill(BaseSkill):
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        base = f"For {account_name}.\n\nACCOUNT DATA:\n{ctx}\n\nUsing ONLY the data above,"

        risk_format = "For each risk provide:\n- Risk: specific technical challenge\n- Severity: RED / AMBER / GREEN\n- Evidence: what in the data signals this risk\n- Pre-sales action: what to validate or demo before close\n- Resolution path: how to mitigate\n\nDo NOT invent risks not in the data. Generate ONLY this section."

        sections = [
            {
                "name": "Integration & Legacy System Risks",
                "prompt": f"{base} identify technical risks related to:\n- Integration requirements mentioned in discovery\n- Legacy/incumbent system dependencies\n\n{risk_format}",
                "max_tokens": 800,
            },
            {
                "name": "Security, Compliance & Technical Unknowns",
                "prompt": f"{base} identify technical risks related to:\n- Security or compliance requirements (SSO, auth, data residency)\n- Any technical unknowns or gaps in discovery\n\n{risk_format}",
                "max_tokens": 800,
            },
        ]

        response = await self.parallel_sections(sections)
        await self.write_output(account_name, "technical_risk.md", response)
        return response
