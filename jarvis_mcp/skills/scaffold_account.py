"""Scaffold Account Skill - Creates new accounts on-demand"""

from jarvis_mcp.skills.base_skill import BaseSkill
from jarvis_mcp.scaffolder import AccountScaffolder
from pathlib import Path


class ScaffoldAccountSkill(BaseSkill):
    """Create new accounts with auto-populated templates"""

    async def generate(self, account_name: str = None, **kwargs) -> str:
        """
        Create a new account scaffold.

        Args:
            account_name: Name of account to create
            **kwargs:
                company_name: Full company name (optional)
                revenue: Company revenue (optional)
                industry: Industry (optional)
                parent_account: Parent account for sub-accounts (optional)

        Returns:
            Confirmation message with account path
        """
        if not account_name:
            return "Error: account_name is required"

        try:
            scaffolder = AccountScaffolder(
                self.config.get_accounts_root()
            )

            # Determine if this is a sub-account
            parent_account = kwargs.get("parent_account")
            parent_path = None

            if parent_account:
                parent_path = self.config.get_account_path(
                    parent_account
                )
                if not parent_path.exists():
                    return (
                        f"Error: Parent account '{parent_account}' not found"
                    )

            # Prepare metadata
            metadata = {
                "company_name": kwargs.get("company_name", account_name),
                "revenue": kwargs.get("revenue"),
                "industry": kwargs.get("industry"),
                "stage": kwargs.get("stage", "Initial Contact"),
                "probability": kwargs.get("probability", 0),
                "deal_size": kwargs.get("deal_size", 0),
            }

            # Scaffold account
            account_path = scaffolder.scaffold_account(
                account_name, parent_path=parent_path, metadata=metadata
            )

            # Build response
            response = (
                f"✓ Account created: {account_name}\n"
                f"Path: {account_path}\n\n"
                f"Created files:\n"
                f"- company_research.md\n"
                f"- discovery.md\n"
                f"- deal_stage.json\n"
                f"- CLAUDE.md\n\n"
            )

            if parent_path:
                response += (
                    f"Sub-account under: {parent_path.name}\n"
                    f"(Inherits company research from parent)\n"
                )

            response += (
                f"\nNext steps:\n"
                f"1. Open the account folder in a cowork\n"
                f"2. Update company_research.md with details\n"
                f"3. Add discovery notes from calls\n"
                f"4. Watch JARVIS auto-generate other files\n"
            )

            return response

        except Exception as e:
            return f"Error creating account: {str(e)}"
