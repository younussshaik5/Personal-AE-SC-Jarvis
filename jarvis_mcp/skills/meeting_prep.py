"""Meeting Preparation Skill"""
from jarvis_mcp.skills.base_skill import BaseSkill


class MeetingPrepSkill(BaseSkill):
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)
        meeting_type = kwargs.get("meeting_type", "")

        prompt = f"""Generate a meeting prep brief for {account_name}{' — ' + meeting_type if meeting_type else ''}.

ACCOUNT DATA:
{ctx}

Using ONLY the data above, build a pre-meeting runsheet:

1. Meeting context: who is attending (from stakeholders in data), purpose, stage
2. What we know: confirmed pain points, requirements, buying signals from discovery
3. What we still need to find out: MEDDPICC gaps, missing information
4. Agenda (ordered by priority — address biggest unknown first):
   - Each agenda item with time allocation and goal
5. Discovery questions to ask — specific to this deal's confirmed pain points
6. Objections to expect — based on concerns mentioned in the data, with handlers
7. Hard ask: what commitment to get by end of this meeting
8. Red flags to watch for

Use the actual stakeholder names and roles from the data. Do NOT invent agenda items not relevant to this deal."""

        response = await self.llm.generate(
            prompt=prompt,
            model_type="reasoning",
            system_prompt=self.grounded_system_prompt(),
            max_tokens=3000,
        )
        await self.write_output(account_name, "meeting_prep.md", response)
        return response
