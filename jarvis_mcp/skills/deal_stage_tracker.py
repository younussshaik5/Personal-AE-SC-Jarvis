"""Deal Stage Management Skill — parallel sections"""
from jarvis_mcp.skills.base_skill import BaseSkill


class DealStageTrackerSkill(BaseSkill):
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)
        new_stage = kwargs.get("stage", "")
        notes = kwargs.get("notes", "")

        extra = ""
        if new_stage:
            extra += f"\nREQUESTED STAGE CHANGE: {new_stage}"
        if notes:
            extra += f"\nNOTES: {notes}"

        base = f"For {account_name}.{extra}\n\nACCOUNT DATA:\n{ctx}\n\nUsing ONLY the data above,"

        sections = [
            {
                "name": "Current Stage Assessment",
                "prompt": f"{base} assess the current deal stage:\n1. Current stage and evidence supporting it\n2. Stage progression history from activities\n3. Whether the requested stage change (if any) is justified by the data\n\nGenerate ONLY this section.",
                "model_type": "reasoning",
                "max_tokens": 800,
            },
            {
                "name": "Stage Readiness & Blockers",
                "prompt": f"{base} analyze:\n1. What criteria are met for the current/next stage\n2. What's blocking advancement to the next stage\n3. Specific actions needed to advance, with owners and dates\n\nGenerate ONLY this section.",
                "model_type": "reasoning",
                "max_tokens": 800,
            },
        ]

        response = await self.parallel_sections(sections)
        return response
