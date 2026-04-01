"""Follow-Up Email Generation Skill"""
from jarvis_mcp.skills.base_skill import BaseSkill


class FollowupEmailSkill(BaseSkill):
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)
        trigger = kwargs.get("trigger", "")

        prompt = f"""Write a follow-up email for {account_name}{' after: ' + trigger if trigger else ''}.

ACCOUNT DATA:
{ctx}

Using ONLY the data above, write TWO follow-up email options:

Option A — Direct (short, action-focused):
- Reference the last activity or meeting from the data
- One specific value point tied to their pain
- Single clear ask with a date

Option B — Consultative (builds relationship):
- Reference the same activity
- Share an insight relevant to their stated problem
- Softer ask — offer value before requesting commitment

Both emails must:
- Use the actual contact name(s) from stakeholder data
- Reference their specific situation (Eloquant renewal, agents, timeline, etc.)
- NOT be generic — every sentence must be traceable to the account data

Sign off as the SC/AE working this deal."""

        response = await self.llm.generate(
            prompt=prompt,
            model_type="text",
            system_prompt=self.grounded_system_prompt(),
            max_tokens=2000,
        )
        await self.write_output(account_name, "followup_email.md", response)
        return response
