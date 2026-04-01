"""Demo Strategy Skill"""
from jarvis_mcp.skills.base_skill import BaseSkill


class DemoStrategySkill(BaseSkill):
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        prompt = f"""Build a demo strategy and flow for {account_name}.

ACCOUNT DATA:
{ctx}

Using ONLY the data above, build a targeted demo plan:

1. Demo objective: what decision/commitment this demo must produce
2. Audience: who is in the room (from stakeholders), what each person cares about
3. Demo flow — ordered by confirmed pain points from discovery (most painful first):
   - Each chapter: feature/capability → pain it solves → proof point
   - Time allocation per chapter
   - Discovery questions to weave in during the demo
4. "Wow moment": the single most compelling thing to show this specific customer
5. What NOT to show: capabilities that are irrelevant or could create confusion
6. Objection handlers for objections mentioned in the data
7. Close: how to end the demo and what to ask for

Tailor every chapter to the confirmed requirements from discovery. Do NOT demo generic features not tied to their stated needs."""

        response = await self.llm.generate(
            prompt=prompt,
            model_type="reasoning",
            system_prompt=self.grounded_system_prompt(),
            max_tokens=3000,
        )
        await self.write_output(account_name, "demo_strategy.md", response)
        return response
