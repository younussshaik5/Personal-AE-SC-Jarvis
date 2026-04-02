"""Meeting Transcription And Analysis Skill — parallel sections"""
from jarvis_mcp.skills.base_skill import BaseSkill


class MeetingSummarySkill(BaseSkill):
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)
        transcript = kwargs.get("transcript", "")

        base = f"For {account_name}.\n\nACCOUNT DATA:\n{ctx}\n\nMEETING TRANSCRIPT:\n{transcript[:6000]}\n\nUsing the data above,"

        sections = [
            {
                "name": "Meeting Summary",
                "prompt": f"{base} write a concise meeting summary:\n1. Attendees and their roles\n2. Key topics discussed\n3. Decisions made\n4. Commitments and action items with owners\n\nGenerate ONLY this section.",
                "model_type": "text",
                "max_tokens": 1000,
            },
            {
                "name": "Deal Impact & MEDDPICC Signals",
                "prompt": f"{base} analyze the meeting's impact:\n1. New MEDDPICC signals found (which dimensions advanced)\n2. How this changes the deal status\n3. New risks or concerns surfaced\n4. Recommended follow-up actions with dates\n\nGenerate ONLY this section.",
                "model_type": "text",
                "max_tokens": 1000,
            },
        ]

        response = await self.parallel_sections(sections)
        await self.write_output(account_name, "meeting_summary.md", response)
        return response
