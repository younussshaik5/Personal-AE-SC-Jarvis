"""Meeting Preparation Skill — parallel sections"""
from jarvis_mcp.skills.base_skill import BaseSkill


class MeetingPrepSkill(BaseSkill):
    MODEL_TYPE = "fast"
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)
        meeting_type = kwargs.get("meeting_type", "")
        mt = f" — {meeting_type}" if meeting_type else ""

        base = f"For {account_name}{mt}.\n\nACCOUNT DATA:\n{ctx}\n\nUsing ONLY the data above,"

        sections = [
            {
                "name": "Meeting Context & What We Know",
                "prompt": f"{base} write:\n1. Meeting context: who is attending (from stakeholders), purpose, current stage\n2. What we know: confirmed pain points, requirements, buying signals from discovery\n3. What we still need to find out: MEDDPICC gaps, missing information\n\nUse actual stakeholder names from the data. Generate ONLY this section.",
                "max_tokens": 1000,
            },
            {
                "name": "Agenda & Discovery Questions",
                "prompt": f"{base} write:\n1. Agenda (ordered by priority — address biggest unknown first):\n   - Each agenda item with time allocation and goal\n2. Discovery questions to ask — specific to this deal's confirmed pain points\n\nGenerate ONLY this section.",
                "max_tokens": 1000,
            },
            {
                "name": "Objection Handlers, Hard Ask & Red Flags",
                "prompt": f"{base} write:\n1. Objections to expect — based on concerns mentioned in the data, with handlers\n2. Hard ask: what commitment to get by end of this meeting\n3. Red flags to watch for\n\nGenerate ONLY this section.",
                "max_tokens": 800,
            },
        ]

        response = await self.parallel_sections(sections)
        await self.write_output(account_name, "meeting_prep.md", response)
        return response
