"""Documentation Generation Skill — parallel sections"""
from jarvis_mcp.skills.base_skill import BaseSkill


class DocumentationSkill(BaseSkill):
    MODEL_TYPE = "writing"
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)
        doc_type = kwargs.get("doc_type", "technical documentation")

        base = f"For {account_name} — {doc_type}.\n\nACCOUNT DATA:\n{ctx}\n\nUsing ONLY the data above,"

        sections = [
            {
                "name": "Overview & Requirements",
                "prompt": f"{base} write the overview section of {doc_type}:\n1. Purpose and scope\n2. Requirements addressed (from discovery)\n3. Audience and prerequisites\n\nGenerate ONLY this section.",
                "model_type": "text",
                "max_tokens": 800,
            },
            {
                "name": "Technical Details & Implementation",
                "prompt": f"{base} write the technical details section of {doc_type}:\n1. Architecture and components\n2. Integration points (from discovery requirements)\n3. Implementation steps and configuration\n\nGenerate ONLY this section.",
                "model_type": "text",
                "max_tokens": 1200,
            },
        ]

        response = await self.parallel_sections(sections)
        return response
