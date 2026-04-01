"""Account Executive Summary Skill"""
from jarvis_mcp.skills.base_skill import BaseSkill


class AccountSummarySkill(BaseSkill):
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        prompt = f"""Generate an executive account summary for {account_name}.

ACCOUNT DATA:
{ctx}

Using ONLY the data above, write a concise executive summary covering:
1. Who the company is and what they do (from company research)
2. The deal — product, ARR, agents, stage, timeline, win probability
3. Key pain points and why they're evaluating (from discovery)
4. Incumbent / competitive situation
5. MEDDPICC status — what's confirmed, what's missing
6. Top 3 risks to closing
7. Recommended next action with a specific date

Do NOT invent any information not in the data above."""

        response = await self.llm.generate(
            prompt=prompt,
            model_type="reasoning",
            system_prompt=self.grounded_system_prompt(),
            max_tokens=3000,
        )
        await self.write_output(account_name, "account_summary.md", response)
        return response
