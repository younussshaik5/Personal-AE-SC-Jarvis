"""MEDDPICC Tracking Skill"""
from jarvis_mcp.skills.base_skill import BaseSkill


class MeddpiccSkill(BaseSkill):
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)

        prompt = f"""Score and analyse MEDDPICC for {account_name}.

ACCOUNT DATA:
{ctx}

Using ONLY the data above, score each of the 8 MEDDPICC dimensions:
Metrics | Economic Buyer | Decision Criteria | Decision Process | Paper Process | Implications/Pain | Champion | Competition

For each dimension:
- Score: RED / AMBER / GREEN
- Evidence: direct quote or reference from the data
- Gap: what is unconfirmed or missing
- Next action: specific question or task to advance this dimension

Then provide:
- Overall deal health: RED / AMBER / GREEN + one-line reason
- Top 3 gaps posing the most risk to closing by the forecast date
- Recommended sequence of actions

Do NOT invent names, competitors, metrics, or timelines not present in the data."""

        response = await self.llm.generate(
            prompt=prompt,
            model_type="reasoning",
            system_prompt=self.grounded_system_prompt(),
            max_tokens=3000,
        )
        await self.write_output(account_name, "meddpicc.md", response)
        return response
