"""CLAUDE.md Loader - Parses and loads CLAUDE.md hierarchically"""

import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ClaudeMdLoader:
    """Loads and parses CLAUDE.md files hierarchically (account-level -> global level)"""

    def __init__(self, accounts_root: Path):
        self.accounts_root = Path(accounts_root).expanduser()
        self.claude_space = accounts_root.parent
        self.global_claude_md = self.claude_space / ".claude" / "CLAUDE.md"

    def load_for_account(self, account_path: Path) -> Dict[str, Any]:
        """
        Load CLAUDE.md hierarchically for an account.

        Priority:
        1. account_path/CLAUDE.md (account-specific)
        2. account_path/Q1/CLAUDE.md (quarter-specific if nested)
        3. ~/.claude/CLAUDE.md (global default)

        Returns:
            Parsed configuration dict
        """
        config = self._get_default_config()

        # Try account-level CLAUDE.md
        account_claude_md = account_path / "CLAUDE.md"
        if account_claude_md.exists():
            logger.info(f"Loading account CLAUDE.md from {account_claude_md}")
            account_config = self._parse_claude_md(account_claude_md)
            config = self._merge_configs(config, account_config)

        # Try parent/quarter-level CLAUDE.md if account is nested
        parent_dir = account_path.parent
        if parent_dir != self.accounts_root:
            parent_claude_md = parent_dir / "CLAUDE.md"
            if parent_claude_md.exists():
                logger.info(
                    f"Loading parent CLAUDE.md from {parent_claude_md}"
                )
                parent_config = self._parse_claude_md(parent_claude_md)
                config = self._merge_configs(config, parent_config)

        # Try global CLAUDE.md
        if self.global_claude_md.exists():
            logger.info(f"Loading global CLAUDE.md from {self.global_claude_md}")
            global_config = self._parse_claude_md(self.global_claude_md)
            config = self._merge_configs(config, global_config)

        return config

    def _parse_claude_md(self, claude_md_path: Path) -> Dict[str, Any]:
        """Parse CLAUDE.md file into configuration dict"""
        config = {
            "cascade_rules": {},
            "model_preferences": {},
            "skill_preferences": {},
            "routing_rules": {},
        }

        try:
            content = claude_md_path.read_text()

            # Parse cascade rules section
            cascade_section = self._extract_section(content, "Cascade Rules")
            if cascade_section:
                config["cascade_rules"] = self._parse_cascade_rules(
                    cascade_section
                )

            # Parse model preferences section
            models_section = self._extract_section(
                content, "Model Preferences"
            )
            if models_section:
                config["model_preferences"] = self._parse_model_preferences(
                    models_section
                )

            # Parse skill preferences section
            skills_section = self._extract_section(
                content, "Skill Preferences"
            )
            if skills_section:
                config["skill_preferences"] = self._parse_skill_preferences(
                    skills_section
                )

            # Parse routing rules section
            routing_section = self._extract_section(content, "Routing Rules")
            if routing_section:
                config["routing_rules"] = self._parse_routing_rules(
                    routing_section
                )

        except Exception as e:
            logger.error(f"Error parsing {claude_md_path}: {e}")

        return config

    def _extract_section(self, content: str, section_name: str) -> Optional[str]:
        """Extract a section from markdown content"""
        # Match "## Section Name" or "### Section Name"
        pattern = rf"^#+\s+{re.escape(section_name)}\s*$"
        lines = content.split("\n")

        section_lines = []
        found = False

        for line in lines:
            if re.match(pattern, line):
                found = True
                continue

            if found:
                # Stop at next section header
                if line.startswith("#"):
                    break
                section_lines.append(line)

        return "\n".join(section_lines).strip() if section_lines else None

    def _parse_cascade_rules(self, section: str) -> Dict[str, List[str]]:
        """Parse cascade rules from markdown section"""
        rules = {}

        # Look for patterns like:
        # - When discovery.updated: refresh demo_strategy, proposal, risk_report
        pattern = r"When\s+(\S+):\s+(.+)"

        for match in re.finditer(pattern, section):
            trigger = match.group(1)
            actions = [
                a.strip() for a in match.group(2).split(",")
            ]
            rules[trigger] = actions

        return rules

    def _parse_model_preferences(self, section: str) -> Dict[str, str]:
        """Parse model preferences from markdown section"""
        prefs = {}

        # Look for patterns like:
        # - Reasoning: Claude Opus
        # - Content generation: Claude Sonnet
        pattern = r"[-•]\s+(.+?):\s+(.+)$"

        for match in re.finditer(pattern, section, re.MULTILINE):
            task = match.group(1).strip()
            model = match.group(2).strip()
            prefs[task.lower()] = model

        return prefs

    def _parse_skill_preferences(self, section: str) -> Dict[str, Dict[str, Any]]:
        """Parse skill-specific preferences from markdown section"""
        prefs = {}

        # Look for skill names and their preferences
        current_skill = None
        for line in section.split("\n"):
            # Match "## SkillName" or "### SkillName"
            if re.match(r"^#+\s+(\w+)\s*$", line):
                current_skill = re.match(r"^#+\s+(\w+)\s*$", line).group(1)
                prefs[current_skill] = {}
            elif current_skill and line.strip().startswith("-"):
                # Parse preference item
                pref_text = line.strip()[1:].strip()
                prefs[current_skill]["preference"] = pref_text

        return prefs

    def _parse_routing_rules(self, section: str) -> Dict[str, str]:
        """Parse skill routing rules from markdown section"""
        rules = {}

        # Look for patterns like:
        # - If ask about pricing: use value_architecture skill first
        pattern = r"If\s+(.+?):\s+(.+)$"

        for match in re.finditer(pattern, section, re.MULTILINE):
            condition = match.group(1).strip()
            action = match.group(2).strip()
            rules[condition] = action

        return rules

    def _merge_configs(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge override config into base config"""
        merged = base.copy()

        for key, value in override.items():
            if isinstance(value, dict) and key in merged:
                merged[key].update(value)
            elif value:  # Only override if not empty
                merged[key] = value

        return merged

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "cascade_rules": {
                "discovery.updated": [
                    "demo_strategy",
                    "proposal",
                    "risk_report",
                    "value_architecture",
                ],
            },
            "model_preferences": {},
            "skill_preferences": {},
            "routing_rules": {},
        }
