"""Extract Intelligence From Conversations Skill — parallel sections"""
from jarvis_mcp.skills.base_skill import BaseSkill


class ConversationExtractorSkill(BaseSkill):
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)
        text = kwargs.get("text", "")

        base = f"For {account_name}.\n\nACCOUNT DATA:\n{ctx}\n\nTEXT TO ANALYZE:\n{text[:5000]}\n\nUsing the data above,"

        sections = [
            {
                "name": "MEDDPICC Signals Extracted",
                "prompt": f"{base} extract all MEDDPICC signals from the text. For each signal found, identify the dimension (M/E/D/D/P/I/C/C), the exact quote or reference, and its significance.\n\nGenerate ONLY this section.",
                "model_type": "text",
                "max_tokens": 1000,
            },
            {
                "name": "Key Intelligence & Action Items",
                "prompt": f"{base} extract:\n1. New stakeholders or roles mentioned\n2. Competitive signals or references\n3. Timeline or urgency indicators\n4. Action items and commitments made\n5. Risks or concerns raised\n\nGenerate ONLY this section.",
                "model_type": "text",
                "max_tokens": 1000,
            },
        ]

        response = await self.parallel_sections(sections)
        await self.write_output(account_name, "conversation_extractor.md", response)
        return response
