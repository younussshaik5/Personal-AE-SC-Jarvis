"""Conversation Analysis Skill — parallel sections"""
from jarvis_mcp.skills.base_skill import BaseSkill


class ConversationSummarizerSkill(BaseSkill):
    MODEL_TYPE = "fast"
    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)
        ctx = self.build_context_block(context, account_name)
        text = kwargs.get("text", "")

        base = f"For {account_name}.\n\nACCOUNT DATA:\n{ctx}\n\nCONVERSATION TEXT:\n{text[:5000]}\n\nUsing the data above,"

        sections = [
            {
                "name": "Conversation Summary",
                "prompt": f"{base} write a concise executive summary of the conversation — who said what, key decisions, and outcomes.\n\nGenerate ONLY this section.",
                "model_type": "text",
                "max_tokens": 800,
            },
            {
                "name": "Impact on Deal & Next Steps",
                "prompt": f"{base} analyze:\n1. How this conversation changes the deal status\n2. New information learned vs what was already known\n3. Action items with owners and dates\n4. Recommended next steps\n\nGenerate ONLY this section.",
                "model_type": "text",
                "max_tokens": 800,
            },
        ]

        response = await self.parallel_sections(sections)
        await self.write_output(account_name, "conversation_summarizer.md", response)
        return response
