"""Competitive Intelligence Skill — parallel sections"""
from jarvis_mcp.skills.base_skill import BaseSkill


class CompetitiveIntelligenceSkill(BaseSkill):
    MODEL_TYPE = "reasoning"
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        base = f"For {account_name}.\n\nACCOUNT DATA:\n{ctx}\n\nUsing ONLY the data above,"

        sections = [
            {
                "name": "Competitor Profile & Customer Motivation",
                "prompt": f"{base} write:\n1. Confirmed competitor(s): names and roles (incumbent, shortlisted, etc.) from deal data\n2. Why the customer is evaluating alternatives — their stated reason from discovery\n3. Competitor's likely strengths in this account\n\nDo NOT add competitors not in the data. Generate ONLY this section.",
                "max_tokens": 1000,
            },
            {
                "name": "Weaknesses, Differentiation & Positioning",
                "prompt": f"{base} write:\n1. Competitor's weaknesses tied to what this customer wants\n2. Our differentiated position for THIS customer's specific requirements\n3. Counter-positioning: how to reframe the evaluation criteria in our favour\n\nGenerate ONLY this section.",
                "max_tokens": 1000,
            },
            {
                "name": "Questions & Risk Assessment",
                "prompt": f"{base} write:\n1. Questions to ask that expose the competitor's gap without naming them\n2. Risk: could the customer stay with the incumbent? What would cause that?\n\nGenerate ONLY this section.",
                "max_tokens": 800,
            },
        ]

        response = await self.parallel_sections(sections)
        return response
