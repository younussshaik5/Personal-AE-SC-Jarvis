"""Follow-Up Email Generation Skill — parallel sections (both options generated simultaneously)"""
from jarvis_mcp.skills.base_skill import BaseSkill


class FollowupEmailSkill(BaseSkill):
    MODEL_TYPE = "fast"
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)
        trigger = kwargs.get("trigger", kwargs.get("context", ""))

        base = f"For {account_name}{' after: ' + trigger if trigger else ''}.\n\nACCOUNT DATA:\n{ctx}\n\nUsing ONLY the data above,"

        sections = [
            {
                "name": "Option A — Direct (Action-Focused)",
                "prompt": f"{base} write a short, direct follow-up email:\n- Reference the last activity or meeting from the data\n- One specific value point tied to their pain\n- Single clear ask with a date\n\nUse actual contact name(s) from stakeholder data. Every sentence must trace to account data. Sign off as the SC/AE. Generate ONLY this email.",
                "model_type": "text",
                "max_tokens": 800,
            },
            {
                "name": "Option B — Consultative (Relationship-Building)",
                "prompt": f"{base} write a consultative follow-up email:\n- Reference the last activity from the data\n- Share an insight relevant to their stated problem\n- Softer ask — offer value before requesting commitment\n\nUse actual contact name(s) from stakeholder data. Every sentence must trace to account data. Sign off as the SC/AE. Generate ONLY this email.",
                "model_type": "text",
                "max_tokens": 800,
            },
        ]

        response = await self.parallel_sections(sections)
        return response
