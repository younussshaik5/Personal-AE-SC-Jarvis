"""Custom Template Generation Skill — parallel sections"""
from jarvis_mcp.skills.base_skill import BaseSkill


class CustomTemplateSkill(BaseSkill):
    MODEL_TYPE = "writing"
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)
        template_name = kwargs.get("template_name", "custom document")
        template_context = kwargs.get("context", "")

        base = f"For {account_name} — {template_name}.\n\nACCOUNT DATA:\n{ctx}"
        if template_context:
            base += f"\n\nADDITIONAL CONTEXT:\n{template_context}"
        base += "\n\nUsing ONLY the data above,"

        sections = [
            {
                "name": f"{template_name} — Part 1: Overview & Context",
                "prompt": f"{base} write the first half of {template_name}:\n- Introduction and purpose\n- Account context and background\n- Key requirements or objectives\n\nGenerate ONLY this section.",
                "model_type": "text",
                "max_tokens": 1200,
            },
            {
                "name": f"{template_name} — Part 2: Details & Recommendations",
                "prompt": f"{base} write the second half of {template_name}:\n- Detailed analysis or content\n- Actionable recommendations\n- Next steps\n\nGenerate ONLY this section.",
                "model_type": "text",
                "max_tokens": 1200,
            },
        ]

        response = await self.parallel_sections(sections)
        await self.write_output(account_name, "custom_template.md", response)
        return response
