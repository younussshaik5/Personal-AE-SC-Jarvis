"""Generate Sales Proposals Skill — parallel sections"""
from jarvis_mcp.skills.base_skill import BaseSkill


class ProposalSkill(BaseSkill):
    MODEL_TYPE = "writing"
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        base = f"For {account_name}.\n\nACCOUNT DATA:\n{ctx}\n\nUsing ONLY the data above,"

        sections = [
            {
                "name": "Executive Summary & Requirements",
                "prompt": f"{base} write:\n1. Executive summary — their situation and why they're evaluating (from discovery)\n2. Their stated requirements — use the actual list from discovery\n\nDo NOT invent requirements. Generate ONLY this section.",
                "max_tokens": 1200,
            },
            {
                "name": "Proposed Solution",
                "prompt": f"{base} write the solution section:\n- Map each confirmed requirement to a specific capability\n- Show how our product addresses their stated pain points\n\nOnly reference requirements from the data. Generate ONLY this section.",
                "max_tokens": 1200,
            },
            {
                "name": "Pricing & Implementation Timeline",
                "prompt": f"{base} write:\n1. Pricing — use the ARR and agent count from deal data\n2. Implementation timeline — tied to their deadline from deal data\n\nUse actual numbers from the data. Generate ONLY this section.",
                "max_tokens": 800,
            },
            {
                "name": "Competitive Positioning & Next Steps",
                "prompt": f"{base} write:\n1. Why us vs the incumbent — use actual competitor from deal data\n2. Next steps — specific, dated actions tied to their timeline\n\nAddress the proposal to the stakeholders named in the data. Generate ONLY this section.",
                "max_tokens": 800,
            },
        ]

        response = await self.parallel_sections(sections)
        await self.write_output(account_name, "proposal.md", response)
        return response
