"""Demo Strategy Skill — parallel sections"""
from jarvis_mcp.skills.base_skill import BaseSkill


class DemoStrategySkill(BaseSkill):
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        base = f"For {account_name}.\n\nACCOUNT DATA:\n{ctx}\n\nUsing ONLY the data above,"

        sections = [
            {
                "name": "Demo Objective & Audience",
                "prompt": f"{base} write:\n1. Demo objective: what decision/commitment this demo must produce\n2. Audience: who is in the room (from stakeholders), what each person cares about\n\nGenerate ONLY this section.",
                "max_tokens": 800,
            },
            {
                "name": "Demo Flow & Wow Moment",
                "prompt": f"{base} write:\n1. Demo flow — ordered by confirmed pain points from discovery (most painful first):\n   - Each chapter: feature/capability → pain it solves → proof point\n   - Time allocation per chapter\n   - Discovery questions to weave in during the demo\n2. \"Wow moment\": the single most compelling thing to show this specific customer\n\nTailor every chapter to confirmed requirements. Do NOT demo generic features. Generate ONLY this section.",
                "max_tokens": 1200,
            },
            {
                "name": "Exclusions, Objection Handlers & Close",
                "prompt": f"{base} write:\n1. What NOT to show: capabilities that are irrelevant or could create confusion\n2. Objection handlers for objections mentioned in the data\n3. Close: how to end the demo and what to ask for\n\nGenerate ONLY this section.",
                "max_tokens": 800,
            },
        ]

        response = await self.parallel_sections(sections)
        await self.write_output(account_name, "demo_strategy.md", response)
        return response
