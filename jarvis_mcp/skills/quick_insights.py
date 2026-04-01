"""Quick Deal Insights Skill"""
from jarvis_mcp.skills.base_skill import BaseSkill


class QuickInsightsSkill(BaseSkill):
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        prompt = f"""Give quick deal insights for {account_name}.

ACCOUNT DATA:
{ctx}

Using ONLY the data above, provide:
1. Deal snapshot: stage, ARR, win prob, forecast date — actual numbers from data
2. Top 3 buying signals confirmed so far
3. Top 3 risks right now (RED items first)
4. #1 next action with a specific date and owner
5. MEDDPICC gaps: list the dimensions that are RED or missing
6. Competitive threat: incumbent name, their strength, our counter

Keep it to bullet points. No padding. No invented facts."""

        response = await self.llm.generate(
            prompt=prompt,
            model_type="fast",
            system_prompt=self.grounded_system_prompt(),
            max_tokens=1500,
        )
        await self.write_output(account_name, "quick_insights.md", response)
        return response
