"""Scope of Work Generation Skill — parallel sections"""
from jarvis_mcp.skills.base_skill import BaseSkill


class SowSkill(BaseSkill):
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        base = f"For {account_name}.\n\nACCOUNT DATA:\n{ctx}\n\nUsing ONLY the data above,"

        sections = [
            {
                "name": "Project Overview & Scope",
                "prompt": f"{base} write a professional SOW covering:\n1. Project overview — what is being implemented (product, plan, agents from deal data)\n2. Scope of work — based on confirmed requirements from discovery\n3. Out of scope — explicitly list anything NOT included\n\nUse the customer's actual name and stakeholders. Generate ONLY this section.",
                "max_tokens": 1200,
            },
            {
                "name": "Deliverables & Timeline",
                "prompt": f"{base} write:\n1. Deliverables with acceptance criteria\n2. Implementation timeline — reverse-engineered from their deadline in deal data\n3. Milestones and checkpoints\n\nGenerate ONLY this section.",
                "max_tokens": 1200,
            },
            {
                "name": "Responsibilities & Commercial Terms",
                "prompt": f"{base} write:\n1. Customer responsibilities (data migration, UAT, stakeholder availability)\n2. Commercial terms summary (ARR from deal data)\n\nReference actual integration requirements from discovery (SSO, APIs, etc.). Generate ONLY this section.",
                "max_tokens": 800,
            },
        ]

        response = await self.parallel_sections(sections)
        await self.write_output(account_name, "sow.md", response)
        return response
