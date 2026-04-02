"""Account Executive Summary Skill — parallel sections"""
from jarvis_mcp.skills.base_skill import BaseSkill


class AccountSummarySkill(BaseSkill):
    MODEL_TYPE = "fast"
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        base = f"For {account_name}.\n\nACCOUNT DATA:\n{ctx}\n\nUsing ONLY the data above,"

        sections = [
            {
                "name": "Company & Deal Overview",
                "prompt": f"{base} write:\n1. Who the company is and what they do (from company research)\n2. The deal — product, ARR, agents, stage, timeline, win probability\n\nDo NOT invent any information. Generate ONLY this section.",
                "max_tokens": 1000,
            },
            {
                "name": "Pain Points & Competitive Situation",
                "prompt": f"{base} write:\n1. Key pain points and why they're evaluating (from discovery)\n2. Incumbent / competitive situation\n\nGenerate ONLY this section.",
                "max_tokens": 800,
            },
            {
                "name": "MEDDPICC Status",
                "prompt": f"{base} write the MEDDPICC status — what's confirmed, what's missing, across all 8 dimensions: Metrics, Economic Buyer, Decision Criteria, Decision Process, Paper Process, Implications/Pain, Champion, Competition.\n\nGenerate ONLY this section.",
                "max_tokens": 800,
            },
            {
                "name": "Risks & Recommended Actions",
                "prompt": f"{base} write:\n1. Top 3 risks to closing\n2. Recommended next action with a specific date\n\nGenerate ONLY this section.",
                "max_tokens": 600,
            },
        ]

        response = await self.parallel_sections(sections)
        await self.write_output(account_name, "account_summary.md", response)
        return response
