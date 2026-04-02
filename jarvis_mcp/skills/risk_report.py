"""Deal Risk Assessment Skill — parallel sections"""
from jarvis_mcp.skills.base_skill import BaseSkill


class RiskReportSkill(BaseSkill):
    MODEL_TYPE = "reasoning"
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        base = f"For {account_name}.\n\nACCOUNT DATA:\n{ctx}\n\nUsing ONLY the data above,"

        sections = [
            {
                "name": "Stakeholder & Competitive Risks",
                "prompt": f"{base} identify risks in the Stakeholder and Competitive categories. For each risk:\n- Risk name\n- Severity: RED / AMBER / GREEN\n- Category\n- Evidence: what in the data signals this risk\n- Mitigation: specific action with owner and deadline\n\nOrder by severity (RED first). Do NOT invent risks not in the data. Generate ONLY this section.",
                "max_tokens": 1000,
            },
            {
                "name": "Technical & Timeline Risks",
                "prompt": f"{base} identify risks in the Technical and Timeline categories. For each risk:\n- Risk name\n- Severity: RED / AMBER / GREEN\n- Category\n- Evidence: what in the data signals this risk\n- Mitigation: specific action with owner and deadline\n\nOrder by severity (RED first). Do NOT invent risks not in the data. Generate ONLY this section.",
                "max_tokens": 1000,
            },
            {
                "name": "Commercial & Process Risks",
                "prompt": f"{base} identify risks in the Commercial and Process categories. For each risk:\n- Risk name\n- Severity: RED / AMBER / GREEN\n- Category\n- Evidence: what in the data signals this risk\n- Mitigation: specific action with owner and deadline\n\nOrder by severity (RED first). Do NOT invent risks not in the data. Generate ONLY this section.",
                "max_tokens": 1000,
            },
            {
                "name": "Overall Risk Assessment",
                "prompt": f"{base} provide:\n- Overall risk rating: RED / AMBER / GREEN\n- Must-resolve before close: the 2–3 risks that will kill the deal if unaddressed\n- Risk trend: improving or worsening based on deal progression\n\nGenerate ONLY this summary section.",
                "max_tokens": 600,
            },
        ]

        response = await self.parallel_sections(sections)
        await self.write_output(account_name, "risk_report.md", response)
        return response
