"""
Meeting Preparation Briefs Skill
"""

from jarvis_mcp.skills.base_skill import BaseSkill


class MeetingPrepSkill(BaseSkill):
    """Meeting preparation briefs"""

    async def generate(self, account_name: str, **kwargs) -> str:
        """
        Generate meeting_prep.

        Args:
            account_name: Account name (e.g., 'Acme Corp')

        Returns:
            Generated content (markdown)
        """
        # Read account context
        context = await self.read_account_files(account_name)

        # Build prompt
        prompt = f"""Generate meeting preparation briefs for {account_name}.

Account Context:
- Company: {context.get('company_research', '')[:500]}...
- Discovery: {context.get('discovery', '')[:500]}...
- Deal Stage: {context.get('deal_stage', 'Unknown')}
- MEDDPICC: {context.get('meddpicc', '')[:300]}...

Create a comprehensive meeting preparation briefs that:
1. Addresses specific account needs
2. References discovery insights
3. Includes actionable recommendations
4. Uses clear formatting (markdown)

Format as professional markdown."""

        # Call NVIDIA
        response = await self.llm.generate(
            model_type="text",
            prompt=prompt,
            context={"account": account_name},
            max_tokens=3000,
        )

        # Write output
        filename = "meeting_prep.md"
        await self.write_output(account_name, filename, response)

        return response
