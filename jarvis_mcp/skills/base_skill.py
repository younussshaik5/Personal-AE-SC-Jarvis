"""BaseSkill - All skills inherit from this"""

import logging
from pathlib import Path
from typing import Dict, Any
from jarvis_mcp.utils.file_utils import read_file, write_file


class BaseSkill:
    """Base class for all skills"""

    def __init__(self, llm_manager, config_manager):
        self.llm = llm_manager
        self.config = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)

    async def execute(self, arguments: Dict[str, Any]) -> str:
        """
        Called by the MCP server with the raw tool arguments dict.
        Extracts account_name and delegates to generate().
        """
        account_name = arguments.get("account_name", "")
        if not account_name:
            return "❌ account_name is required."
        # Pass remaining args as kwargs (transcript, context, stage, etc.)
        extra = {k: v for k, v in arguments.items() if k != "account_name"}
        try:
            result = await self.generate(account_name, **extra)
            return result or "✅ Done."
        except Exception as e:
            self.logger.error(f"execute() failed: {e}", exc_info=True)
            return f"❌ Error: {e}"

    async def read_account_files(self, account_name: str) -> Dict[str, str]:
        """Read all .md files in account directory"""
        account_path = self.config.get_account_path(account_name)
        if not account_path.exists():
            self.logger.warning(f"Account path doesn't exist: {account_path}")
            return {}

        context = {}
        for md_file in sorted(account_path.glob("*.md")):
            key = md_file.stem
            content = await read_file(md_file)
            context[key] = content

        return context

    async def write_output(self, account_name: str, filename: str, content: str) -> bool:
        """Write output to account directory"""
        account_path = self.config.get_account_path(account_name)
        account_path.mkdir(parents=True, exist_ok=True)
        output_path = account_path / filename
        success = await write_file(output_path, content)
        if success:
            self.logger.info(f"Wrote {filename} for {account_name}")
        return success

    async def generate(self, account_name: str, **kwargs) -> str:
        """Override in subclasses"""
        raise NotImplementedError()
