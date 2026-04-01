"""JARVIS MCP Server - Main entry point with zero-manual-creation features"""

import json
import logging
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

logger = logging.getLogger(__name__)


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

        if not resolved_account:
            return "Error: Could not determine account. Provide account name or open account folder in cowork."

        # Step 2: Get account path with hierarchy support
        account_path = self.account_hierarchy.find_account(resolved_account)

        if not account_path:
            # Check if this is a new account - offer to scaffold
            if tool_name == "scaffold_account":
                return await self._handle_scaffold_account(
                    resolved_account, **kwargs
                )
            return f"Account '{resolved_account}' not found."

        # Step 3: Load account context (including parent if sub-account)
        account_context = self.account_hierarchy.get_account_context(account_path)

        # Step 4: Load CLAUDE.md settings
        claude_settings = self.claude_md_loader.load_for_account(account_path)

        # Step 5: Call the skill
        if tool_name not in self.skills:
            return f"Skill '{tool_name}' not found."

        skill = self.skills[tool_name]

        try:
            # Pass account path instead of name for better context
            result = await skill.generate(
                account_name=resolved_account,
                account_path=account_path,
                account_context=account_context,
                claude_settings=claude_settings,
                **kwargs
            )

            # Step 6: Track interaction for CLAUDE.md evolution
            await self._track_interaction(
                account_path,
                tool_name,
                result,
                **kwargs
            )

            return result

        except Exception as e:
            logger.error(f"Error calling skill {tool_name}: {e}")
            return f"Error: {str(e)}"

    def _resolve_account(self, explicit_account: Optional[str]) -> Optional[str]:
        """
        Resolve account name with priority:
        1. Explicit account (highest priority)
        2. Context detected from current folder
        3. Environment variable JARVIS_ACCOUNT
        """
        # Explicit account takes priority
        if explicit_account:
            return explicit_account

        # Detect from context (current folder)
        context = self.context_detector.detect_account_context()
        if context:
            logger.info(f"Detected account from context: {context['account_name']}")
            return context['account_name']

        # Environment variable
        import os
        env_account = os.getenv("JARVIS_ACCOUNT")
        if env_account:
            return env_account

        return None

    async def _handle_scaffold_account(
        self,
        account_name: str,
        **kwargs
    ) -> str:
        """Handle account scaffolding"""
        try:
            parent_account = kwargs.get("parent_account")
            parent_path = None

            if parent_account:
                parent_path = self.account_hierarchy.find_account(parent_account)
                if not parent_path:
                    return f"Parent account '{parent_account}' not found."

            account_path = self.scaffolder.scaffold_account(
                account_name,
                parent_path=parent_path,
                metadata=kwargs
            )

            # Refresh hierarchy cache
            self.account_hierarchy.refresh_cache()

            result = (
                f"✓ Account created: {account_name}\n"
                f"Path: {account_path}\n\n"
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
                "24_skills"
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
# MCP PROTOCOL IMPLEMENTATION - Server Startup
# ============================================================================

import asyncio
from mcp.server import Server
from mcp.types import Tool, TextContent, ToolResult


def create_mcp_server():
    """Create and configure MCP server with all tools"""
    server = Server("jarvis-mcp")
    jarvis = JarvisServer()

    # Register all skills as MCP tools
    @server.list_tools()
    async def list_tools():
        """List all available JARVIS skills as MCP tools"""
        tools = []
        for skill_name in jarvis.skills.keys():
            tools.append(
                Tool(
                    name=skill_name,
                    description=f"JARVIS skill: {skill_name}",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "account": {
                                "type": "string",
                                "description": "Account name (optional, auto-detected if in account folder)"
                            }
                        }
                    }
                )
            )
        
        # Add system tools
        system_tools = [
            Tool(
                name="list_accounts",
                description="List all accounts and their paths",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="get_account_info",
                description="Get detailed information about an account",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "account_name": {
                            "type": "string",
                            "description": "Name of the account"
                        }
                    }
                }
            ),
            Tool(
                name="server_status",
                description="Get JARVIS server status and statistics",
                inputSchema={"type": "object", "properties": {}}
            )
        ]
        
        return tools + system_tools

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> ToolResult:
        """Execute a tool/skill"""
        try:
            # System tools
            if name == "list_accounts":
                accounts = jarvis.list_accounts()
                return ToolResult(
                    content=[TextContent(type="text", text=json.dumps(accounts, indent=2))],
                    is_error=False
                )
            
            elif name == "get_account_info":
                account_name = arguments.get("account_name")
                info = jarvis.get_account_info(account_name)
                if info:
                    return ToolResult(
                        content=[TextContent(type="text", text=json.dumps(info, indent=2))],
                        is_error=False
                    )
                else:
                    return ToolResult(
                        content=[TextContent(type="text", text=f"Account not found: {account_name}")],
                        is_error=True
                    )
            
            elif name == "server_status":
                status = jarvis.get_server_status()
                return ToolResult(
                    content=[TextContent(type="text", text=json.dumps(status, indent=2))],
                    is_error=False
                )
            
            # Skill tools
            elif name in jarvis.skills:
                account = arguments.get("account")
                result = await jarvis.handle_tool_call(name, account=account, **arguments)
                return ToolResult(
                    content=[TextContent(type="text", text=result)],
                    is_error=False
                )
            
            else:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                    is_error=True
                )
        
        except Exception as e:
            logger.error(f"Tool call error: {e}")
            return ToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                is_error=True
            )

    return server


async def main():
    """Start the MCP server"""
    logger.info("Starting JARVIS MCP Server...")
    
    server = create_mcp_server()
    
    # Run on stdio
    async with server.stdio_server() as streams:
        logger.info("✓ JARVIS MCP Server running on stdio")
        logger.info("✓ Waiting for Claude Desktop to connect...")
        await server.wait_for_shutdown()
    
    logger.info("JARVIS MCP Server shutdown")


if __name__ == "__main__":
    # When run as: python3 mcp_server.py
    # Claude Desktop will use stdio for communication
    asyncio.run(main())
