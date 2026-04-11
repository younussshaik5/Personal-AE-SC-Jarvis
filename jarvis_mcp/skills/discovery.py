"""Discovery Call Management Skill — parallel sections"""
from jarvis_mcp.skills.base_skill import BaseSkill


class DiscoverySkill(BaseSkill):
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        base = f"For {account_name}.\n\nACCOUNT DATA:\n{ctx}\n\nUsing ONLY the data above,"

        sections = [
            {
                "name": "Discovery Framework & Key Questions",
                "prompt": f"{base} generate discovery call questions organized by MEDDPICC dimension. For each dimension, provide 2-3 targeted questions based on what's already known vs what's missing from the account data.\n\nGenerate ONLY this section.",
                "model_type": "text",
                "max_tokens": 1200,
            },
            {
                "name": "Pain Mapping & Qualification Gaps",
                "prompt": f"{base} write:\n1. Confirmed pain points from discovery notes\n2. Qualification gaps — what's still unknown\n3. Recommended discovery sequence for the next call\n\nGenerate ONLY this section.",
                "model_type": "text",
                "max_tokens": 1000,
            },
        ]

        response = await self.parallel_sections(sections)
        return response
