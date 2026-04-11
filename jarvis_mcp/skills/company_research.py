"""Company Research Skill — auto-populates company_research.md from account intel."""
from jarvis_mcp.skills.base_skill import BaseSkill


class CompanyResearchSkill(BaseSkill):
    MODEL_TYPE = "reasoning"

    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        prompt = (
            f"For {account_name}.\n\nACCOUNT DATA:\n{ctx}\n\n"
            "Using ONLY the data above, produce a structured company research profile "
            "in the exact markdown format below. "
            "For any field not confirmed in the data, write the field label followed by "
            "'TBD — [specific question to ask]'. Never leave a field blank.\n\n"
            "## Company Overview\n"
            "- **Company Name:** \n"
            "- **Industry:** \n"
            "- **Revenue:** \n"
            "- **Employees:** \n"
            "- **HQ:** \n"
            "- **Founded:** \n\n"
            "## Business Model\n"
            "- **Primary Revenue Stream:** \n"
            "- **Customer Base:** \n"
            "- **Market Position:** \n\n"
            "## Current Pain Points\n"
            "List every confirmed pain point with a one-line impact statement.\n\n"
            "## Tech Stack & Technical Environment\n"
            "What is known about current systems, platforms, integrations.\n\n"
            "## Competitive Landscape\n"
            "Incumbent, alternatives evaluated, or status of any prior solution.\n\n"
            "## Budget & Timeline\n"
            "Known or estimated budget range and project timeline.\n\n"
            "## Key Contacts\n"
            "Every named stakeholder: Name — Title (Role in deal).\n\n"
            "## Strategic Initiatives\n"
            "Any stated business goals, digital transformation efforts, or compliance mandates.\n\n"
            "Generate ONLY this profile. Do NOT repeat the section headings in bullet points."
        )

        return await self.llm.generate(
            prompt=prompt,
            model_type=self.MODEL_TYPE,
            system_prompt=self.grounded_system_prompt(),
            max_tokens=2000,
        )
