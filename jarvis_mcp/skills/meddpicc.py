"""MEDDPICC Tracking Skill — parallel sections (8 dimensions fired simultaneously)"""
from jarvis_mcp.skills.base_skill import BaseSkill


class MeddpiccSkill(BaseSkill):
    MODEL_TYPE = "reasoning"
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        base = f"For {account_name}.\n\nACCOUNT DATA:\n{ctx}\n\nUsing ONLY the data above,"

        dim_instruction = (
            "For this dimension provide ALL of the following:\n"
            "- **Score:** RED / AMBER / GREEN\n"
            "- **Evidence:** direct quote or reference from the data (if none, state 'No data found')\n"
            "- **Gap:** what is unconfirmed or missing\n"
            "- **Next action:** specific discovery question to advance this dimension\n\n"
            "CRITICAL: You MUST produce content for every field above. "
            "If the data is TBD or missing, score RED, state what is absent, and write the exact question to ask. "
            "Do NOT invent facts. Do NOT leave any field blank. Generate ONLY this dimension."
        )

        sections = [
            {
                "name": "Metrics",
                "prompt": f"{base} score the MEDDPICC dimension **Metrics** — quantified business outcomes, ROI, cost savings.\n\n{dim_instruction}",
                "max_tokens": 500,
            },
            {
                "name": "Economic Buyer",
                "prompt": f"{base} score the MEDDPICC dimension **Economic Buyer** — who has budget authority, final sign-off power.\n\n{dim_instruction}",
                "max_tokens": 500,
            },
            {
                "name": "Decision Criteria",
                "prompt": f"{base} score the MEDDPICC dimension **Decision Criteria** — what requirements they're evaluating against.\n\n{dim_instruction}",
                "max_tokens": 500,
            },
            {
                "name": "Decision Process",
                "prompt": f"{base} score the MEDDPICC dimension **Decision Process** — steps, timeline, approvals needed to buy.\n\n{dim_instruction}",
                "max_tokens": 500,
            },
            {
                "name": "Paper Process",
                "prompt": f"{base} score the MEDDPICC dimension **Paper Process** — legal, security review, procurement, contract.\n\n{dim_instruction}",
                "max_tokens": 500,
            },
            {
                "name": "Implications / Pain",
                "prompt": f"{base} score the MEDDPICC dimension **Implications / Pain** — what happens if they don't act, confirmed pain points.\n\n{dim_instruction}",
                "max_tokens": 500,
            },
            {
                "name": "Champion",
                "prompt": f"{base} score the MEDDPICC dimension **Champion** — internal advocate who is selling on our behalf.\n\n{dim_instruction}",
                "max_tokens": 500,
            },
            {
                "name": "Competition",
                "prompt": f"{base} score the MEDDPICC dimension **Competition** — who else is being evaluated, incumbent status.\n\n{dim_instruction}",
                "max_tokens": 500,
            },
            {
                "name": "Overall Deal Health & Action Plan",
                "prompt": f"{base} provide a MEDDPICC summary:\n- Overall deal health: RED / AMBER / GREEN + one-line reason\n- Top 3 gaps posing the most risk to closing by the forecast date\n- Recommended sequence of actions to close the gaps\n\nGenerate ONLY this summary.",
                "max_tokens": 600,
            },
        ]

        response = await self.parallel_sections(sections)
        return response
