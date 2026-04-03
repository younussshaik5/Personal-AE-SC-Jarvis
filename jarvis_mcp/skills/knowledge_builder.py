"""Build Interconnected Knowledge Graphs Skill — parallel sections"""
from jarvis_mcp.skills.base_skill import BaseSkill


class KnowledgeBuilderSkill(BaseSkill):
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        base = f"For {account_name}.\n\nACCOUNT DATA:\n{ctx}\n\nUsing ONLY the data above,"

        sections = [
            {
                "name": "Stakeholder Map & Relationships",
                "prompt": f"{base} build a stakeholder knowledge graph:\n- All named people, their roles, and influence\n- Relationships between stakeholders (reports to, influences, blocks)\n- Champion / detractor / neutral classification\n- Power/influence grid\n\nGenerate ONLY this section.",
                "model_type": "reasoning",
                "max_tokens": 1000,
            },
            {
                "name": "Deal Knowledge Graph",
                "prompt": f"{base} build a deal knowledge graph connecting:\n- Pain points → requirements → capabilities → value\n- Competitor → their strengths → our counter\n- Timeline milestones → dependencies → risks\n- MEDDPICC dimensions → evidence → gaps\n\nPresent as structured relationships. Generate ONLY this section.",
                "model_type": "reasoning",
                "max_tokens": 1000,
            },
        ]

        response = await self.parallel_sections(sections)
        return response
