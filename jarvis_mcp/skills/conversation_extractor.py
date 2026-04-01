"""
Extract Intelligence From Conversations Skill
"""

from jarvis_mcp.skills.base_skill import BaseSkill


class ConversationExtractorSkill(BaseSkill):
    """Extract intelligence from conversations"""

    async def generate(self, account_name: str, **kwargs) -> str:
        """
        Generate conversation_extractor.

        Args:
            account_name: Account name (e.g., 'Acme Corp')

        Returns:
            Generated content (markdown)
        """
        # Read account context
        context = await self.read_account_files(account_name)

        # Build prompt
        prompt = f"""Generate extract intelligence from conversations for {account_name}.

Account Context:
- Company: {context.get('company_research', '')[:500]}...
- Discovery: {context.get('discovery', '')[:500]}...
- Deal Stage: {context.get('deal_stage', 'Unknown')}
- MEDDPICC: {context.get('meddpicc', '')[:300]}...

Create a comprehensive extract intelligence from conversations that:
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
        filename = "conversation_extractor.md"
        await self.write_output(account_name, filename, response)

        return response
