"""BaseSkill - All skills inherit from this"""

import logging
from pathlib import Path
from typing import Dict
from jarvis_mcp.utils.file_utils import read_file, write_file


class BaseSkill:
    """Base class for all skills"""

    def __init__(self, llm_manager, config_manager):
        self.llm = llm_manager
        self.config = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)

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
        output_path = account_path / filename
        success = await write_file(output_path, content)
        if success:
            self.logger.info(f"Wrote {filename} for {account_name}")
        return success

    async def generate(self, account_name: str, **kwargs) -> str:
        """Override in subclasses"""
        raise NotImplementedError()
