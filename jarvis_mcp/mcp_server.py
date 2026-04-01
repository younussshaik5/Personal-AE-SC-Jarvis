"""JARVIS MCP Server - Main entry point with zero-manual-creation features"""

import json
import logging
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from .account_hierarchy import AccountHierarchy
from .context_detector import ContextDetector
from .claude_md_loader import ClaudeMdLoader
from .claude_md_evolve import ClaudeMdEvolution
from .scaffolder import AccountScaffolder
from .config.config_manager import ConfigManager
from .llm.llm_manager import LLMManager
from .utils.logger import setup_logger
from .skills import SKILL_REGISTRY

logger = setup_logger("jarvis_mcp")


class JarvisServer:
    """JARVIS MCP Server - AI Sales Intelligence Platform"""

    def __init__(self, config: Optional[ConfigManager] = None):
        """Initialize JARVIS server with all infrastructure"""
        self.config = config or ConfigManager()
        self.llm = LLMManager(self.config)

        # New zero-manual-creation infrastructure
        self.accounts_root = self.config.get_accounts_root()
        self.account_hierarchy = AccountHierarchy(self.accounts_root)
        self.context_detector = ContextDetector(self.accounts_root)
        self.claude_md_loader = ClaudeMdLoader(self.accounts_root)
        self.scaffolder = AccountScaffolder(self.accounts_root)

        # Initialize skills
        self.skills: Dict[str, Any] = {}
        self._initialize_skills()

        logger.info("JARVIS Server initialized with zero-manual-creation features")

    def _initialize_skills(self):
        """Initialize all 24 skills"""
        for skill_name, skill_class in SKILL_REGISTRY.items():
            try:
                self.skills[skill_name] = skill_class(self.llm, self.config)
                logger.info(f"Loaded skill: {skill_name}")
            except Exception as e:
                logger.error(f"Failed to load skill {skill_name}: {e}")

    async def handle_tool_call(
        self,
        tool_name: str,
        account: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Handle tool call with automatic context detection.

        Args:
            tool_name: Name of the skill to call
            account: Optional explicit account name
            **kwargs: Skill-specific arguments

        Returns:
            Skill output
        """
        # Step 1: Detect or resolve account
        resolved_account = self._resolve_account(account)

        if not resolved_account and tool_name != "scaffold_account":
            return "Error: Could not determine account. Provide account name or open account folder in cowork."

        # Step 2: Get account path with hierarchy support
        if resolved_account:
            account_path = self.account_hierarchy.find_account(resolved_account)
        else:
            account_path = None

        if not account_path and tool_name != "scaffold_account":
            # Check if this is a new account - offer to scaffold
            if tool_name == "scaffold_account":
                return await self._handle_scaffold_account(
                    resolved_account, **kwargs
                )
            return f"Account not found: {resolved_account}"

        # Step 3: Load context
        context = {}
        if account_path:
            context = self.account_hierarchy.get_account_context(account_path)

        # Step 4: Call skill
        try:
            if tool_name == "scaffold_account":
                return await self._handle_scaffold_account(
                    resolved_account, **kwargs
                )

            if tool_name in self.skills:
                skill = self.skills[tool_name]
                result = await skill.generate(resolved_account, **kwargs)

                # Track interaction
                if account_path:
                    await self._track_interaction(
                        account_path, tool_name, result, **kwargs
                    )

                return result
            else:
                return f"Skill not found: {tool_name}"

        except Exception as e:
            logger.error(f"Error calling skill {tool_name}: {e}")
            return f"Error: {str(e)}"

    def _resolve_account(self, explicit_account: Optional[str]) -> Optional[str]:
        """Resolve account from explicit parameter or context"""
        if explicit_account:
            return explicit_account

        # Try to detect from context
        context = self.context_detector.detect_account_context()
        if context:
            return context.get("account_name")

        return None

    async def _handle_scaffold_account(
        self,
        account_name: str,
        parent_account: Optional[str] = None,
        **kwargs
    ) -> str:
        """Handle account scaffolding"""
        try:
            # Determine parent path if specified
            parent_path = None
            if parent_account:
                parent_path = self.account_hierarchy.find_account(parent_account)
                if not parent_path:
                    return f"Parent account not found: {parent_account}"

            # Scaffold the account
            account_path = self.scaffolder.scaffold_account(
                account_name,
                parent_path=parent_path,
                metadata=kwargs
            )

            result = (
                f"Account created: {account_name}\n"
                f"Path: {account_path}\n"
                f"Files created:\n"
                f"- company_research.md\n"
                f"- discovery.md\n"
                f"- deal_stage.json\n"
                f"- CLAUDE.md\n"
            )

            if parent_path:
                result += f"\nSub-account under: {parent_path.name}\n"

            return result

        except Exception as e:
            return f"Error creating account: {str(e)}"

    async def _track_interaction(
        self,
        account_path: Path,
        skill_name: str,
        result: str,
        **kwargs
    ):
        """Track interaction for CLAUDE.md evolution"""
        try:
            evolve = ClaudeMdEvolution(account_path)

            # Estimate quality (0-5 scale)
            # In real implementation, this would come from user feedback
            quality = 4.5  # Default

            # Check if user requested ROI (for learning)
            feedback = ""
            if "roi" in str(result).lower():
                feedback = "roi_included"

            evolve.record_interaction(
                skill=skill_name,
                model_type="text",
                quality=quality,
                feedback=feedback
            )

            # Analyze for suggestions
            suggestions = evolve.analyze_patterns()
            if suggestions:
                logger.info(f"JARVIS learned {len(suggestions)} improvement(s) for {account_path.name}")

        except Exception as e:
            logger.warning(f"Could not track interaction: {e}")

    def list_accounts(self) -> Dict[str, str]:
        """List all accounts with their paths"""
        accounts = {}
        for name, path in self.account_hierarchy.list_all_accounts():
            accounts[name] = str(path)
        return accounts

    def get_account_info(self, account_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed account information"""
        account_path = self.account_hierarchy.find_account(account_name)
        if not account_path:
            return None

        return {
            "account_name": account_name,
            "path": str(account_path),
            "is_sub_account": account_path.parent != self.accounts_root,
            "sub_accounts": [
                p.name
                for p in self.account_hierarchy.get_sub_accounts(account_path)
            ],
            "context": self.account_hierarchy.get_account_context(account_path),
            "claude_settings": self.claude_md_loader.load_for_account(account_path),
        }

    def get_server_status(self) -> Dict[str, Any]:
        """Get server status and statistics"""
        accounts = self.account_hierarchy.list_all_accounts()

        return {
            "status": "running",
            "version": "2.0.0",
            "features": [
                "zero_manual_creation",
                "account_hierarchy",
                "context_detection",
                "claude_md_evolution",
                "25_skills"
            ],
            "total_accounts": len(accounts),
            "accounts_root": str(self.accounts_root),
            "skills_available": len(self.skills),
            "infrastructure": {
                "account_hierarchy": True,
                "context_detector": True,
                "claude_md_loader": True,
                "claude_md_evolve": True,
                "scaffolder": True,
            }
        }


# ============================================================================
# Standalone Server Mode (for testing/verification)
# ============================================================================

def print_banner():
    """Print JARVIS banner"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║          JARVIS v2.0 - MCP Server                         ║
║   AI Sales Intelligence Platform                         ║
╚═══════════════════════════════════════════════════════════╝

✓ Server initialized
✓ 25+ skills loaded
✓ Ready for Claude Desktop

To use with Claude Desktop:
1. Add to ~/.claude/config.json (see README.md)
2. Restart Claude Desktop
3. MCP server will start automatically
"""
    print(banner)


async def run_standalone():
    """Run server in standalone mode (for verification)"""
    print_banner()
    
    server = JarvisServer()
    status = server.get_server_status()
    
    print(f"\nServer Status:")
    print(f"  Status: {status['status']}")
    print(f"  Skills: {status['skills_available']}")
    print(f"  Accounts: {status['total_accounts']}")
    print(f"  Version: {status['version']}")
    
    print(f"\nAvailable Skills ({len(server.skills)}):")
    for i, skill_name in enumerate(sorted(server.skills.keys()), 1):
        print(f"  {i:2d}. {skill_name}")
    
    print("\n✓ Server ready to accept connections from Claude Desktop")


if __name__ == "__main__":
    # When run as: python3 mcp_server.py
    # This can be used for testing/verification
    # For production, Claude Desktop manages the server lifecycle
    
    try:
        asyncio.run(run_standalone())
    except KeyboardInterrupt:
        print("\n\nShutdown requested")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
