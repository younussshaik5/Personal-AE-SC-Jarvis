"""Deal Risk Assessment Skill"""
from jarvis_mcp.skills.base_skill import BaseSkill


class RiskReportSkill(BaseSkill):
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        prompt = f"""Generate a deal risk report for {account_name}.

ACCOUNT DATA:
{ctx}

Using ONLY the data above, identify every risk present in this deal. For each risk:
- Risk name
- Severity: RED / AMBER / GREEN
- Category: Stakeholder | Competitive | Technical | Timeline | Commercial | Process
- Evidence: what in the data signals this risk
- Mitigation: specific action with owner and deadline

Order risks by severity (RED first).

Then provide:
- Overall risk rating: RED / AMBER / GREEN
- Must-resolve before close: the 2–3 risks that will kill the deal if unaddressed
- Risk trend: improving or worsening based on deal progression

Do NOT invent risks not evidenced in the data."""

        response = await self.llm.generate(
            prompt=prompt,
            model_type="reasoning",
            system_prompt=self.grounded_system_prompt(),
            max_tokens=3000,
        )
        await self.write_output(account_name, "risk_report.md", response)
        return response
