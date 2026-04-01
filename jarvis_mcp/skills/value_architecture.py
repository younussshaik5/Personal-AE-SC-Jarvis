"""
Roi And Tco Analysis Skill
"""

from jarvis_mcp.skills.base_skill import BaseSkill


class ValueArchitectureSkill(BaseSkill):
    """ROI and TCO analysis"""

    async def generate(self, account_name: str, **kwargs) -> str:
        """
        Generate value_architecture.

        Args:
            account_name: Account name (e.g., 'Acme Corp')

        Returns:
            Generated content (markdown)
        """
        # Read account context
        context = await self.read_account_files(account_name)

        # Build prompt
        prompt = f"""Generate roi and tco analysis for {account_name}.

Account Context:
- Company: {context.get('company_research', '')[:500]}...
- Discovery: {context.get('discovery', '')[:500]}...
- Deal Stage: {context.get('deal_stage', 'Unknown')}
- MEDDPICC: {context.get('meddpicc', '')[:300]}...

Create a comprehensive roi and tco analysis that:
1. Addresses specific account needs
2. References discovery insights
3. Includes actionable recommendations
4. Uses clear formatting (markdown)

Format as professional markdown."""

        # Call NVIDIA
        response = await self.llm.generate(
            model_type="long_context",
            prompt=prompt,
            context={"account": account_name},
            max_tokens=3000,
        )

        # Write output
        filename = "value_architecture.md"
        await self.write_output(account_name, filename, response)

        return response
