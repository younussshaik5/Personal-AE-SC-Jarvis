"""Solution Architecture Diagrams Skill — parallel sections"""
from jarvis_mcp.skills.base_skill import BaseSkill


class ArchitectureDiagramSkill(BaseSkill):
    MODEL_TYPE = "writing"
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        base = f"For {account_name}.\n\nACCOUNT DATA:\n{ctx}\n\nUsing ONLY the data above,"

        sections = [
            {
                "name": "Architecture Overview",
                "prompt": f"{base} describe the solution architecture for this account — components, integrations, and data flows based on their requirements from discovery.\n\nGenerate ONLY this section.",
                "model_type": "reasoning",
                "max_tokens": 800,
            },
            {
                "name": "Mermaid.js Diagram",
                "prompt": f"{base} generate a Mermaid.js diagram (graph TD) showing the solution architecture for this account. Include:\n- Customer systems (from discovery/company research)\n- Our platform components\n- Integration points (SSO, APIs, etc. from requirements)\n- Data flows\n\nOutput valid Mermaid.js code in a code block. Generate ONLY this diagram.",
                "model_type": "reasoning",
                "max_tokens": 1000,
            },
        ]

        response = await self.parallel_sections(sections)
        await self.write_output(account_name, "architecture_diagram.md", response)
        return response
