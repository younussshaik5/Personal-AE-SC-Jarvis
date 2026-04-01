"""
ClaudeMdLoader - Parses CLAUDE.md files for configuration and cascade rules.
Supports hierarchical parsing (account-level → global level).
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime


class ClaudeMdLoader:
    """
    Loads and parses CLAUDE.md configuration files.
    Supports account-level and global-level configuration.
    """

    def __init__(self, account_path: Optional[str] = None):
        """Initialize loader"""
        self.logger = logging.getLogger(__name__)
        self.account_path = Path(account_path) if account_path else None
        
        # Config cache
        self._account_config = None
        self._global_config = None
        
    def load_config(self, account_path: Optional[str] = None, force_reload: bool = False) -> Dict[str, Any]:
        """
        Load CLAUDE.md configuration, cascading from account → global.
        
        Returns:
            Merged configuration dict
        """
        if not force_reload and self._account_config:
            return self._account_config
            
        if account_path:
            self.account_path = Path(account_path)
            
        config = {}
        
        # Load global config first (base)
        global_config = self.load_global_config()
        config.update(global_config)
        
        # Overlay account config (overwrites global)
        if self.account_path:
            account_config = self.load_account_config(self.account_path)
            config.update(account_config)
            
        self._account_config = config
        return config
        
    def load_global_config(self) -> Dict[str, Any]:
        """Load global CLAUDE.md configuration"""
        # Project root CLAUDE.md (works for any clone location)
        project_root = Path(__file__).parent.parent
        global_path = Path(os.getenv("JARVIS_CLAUDE_MD", str(project_root / "CLAUDE.md")))
        
        if global_path.exists():
            return self._parse_claude_md(global_path)
        else:
            self.logger.debug("No global CLAUDE.md found")
            return {}
            
    def load_account_config(self, account_path: Path) -> Dict[str, Any]:
        """Load account-specific CLAUDE.md configuration"""
        account_claude = account_path / "CLAUDE.md"
        
        if account_claude.exists():
            return self._parse_claude_md(account_claude)
        else:
            self.logger.debug(f"No account CLAUDE.md found at {account_path}")
            return {}
            
    def _parse_claude_md(self, claude_path: Path) -> Dict[str, Any]:
        """Parse CLAUDE.md and extract configuration"""
        try:
            with open(claude_path, 'r') as f:
                content = f.read()
        except Exception as e:
            self.logger.error(f"Could not read {claude_path}: {e}")
            return {}
            
        config = {
            'path': str(claude_path),
            'model_assignments': {},
            'cascade_rules': {},
            'skill_routes': {},
            'evolution_suggestions': [],
            'metadata': {}
        }
        
        # Parse model assignments section
        # Format:
        # ## Models
        # - proposal: claude-opus
        # - discovery: claude-sonnet
        model_section = self._extract_section(content, "Models")
        if model_section:
            config['model_assignments'] = self._parse_key_value_list(model_section)
            
        # Parse cascade rules
        # Format:
        # ## Cascades
        # - opportunity_size < 100K: use_quick_models
        # - urgency = critical: escalate_to_best
        cascade_section = self._extract_section(content, "Cascades")
        if cascade_section:
            config['cascade_rules'] = self._parse_cascade_rules(cascade_section)
            
        # Parse skill routes
        # Format:
        # ## Skills
        # proposal: ["discovery", "battlecard", "risk"]
        skill_section = self._extract_section(content, "Skills")
        if skill_section:
            config['skill_routes'] = self._parse_skill_routes(skill_section)
            
        # Parse evolution suggestions
        # Format:
        # ## Evolution Suggestions
        # - [CRITICAL] proposal model failing > 20% → use claude-opus
        # - [HIGH] discovery quality < 3.5 → increase prompt specificity
        evolution_section = self._extract_section(content, "Evolution Suggestions")
        if evolution_section:
            config['evolution_suggestions'] = self._parse_evolution_suggestions(evolution_section)
            
        # Parse metadata
        # Format:
        # ## Metadata
        # - last_updated: 2026-04-01
        # - optimized_by: config_evolver
        metadata_section = self._extract_section(content, "Metadata")
        if metadata_section:
            config['metadata'] = self._parse_key_value_list(metadata_section)
            
        self.logger.info(f"Loaded CLAUDE.md from {claude_path}")
        return config
        
    def _extract_section(self, content: str, section_name: str) -> Optional[str]:
        """Extract content between ## SectionName and next ##"""
        pattern = rf"##\s+{section_name}\s*\n(.*?)(?=##|\Z)"
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        return match.group(1) if match else None
        
    def _parse_key_value_list(self, section: str) -> Dict[str, str]:
        """Parse simple key: value list"""
        result = {}
        for line in section.split('\n'):
            line = line.strip()
            if line.startswith('- '):
                line = line[2:]
            if ':' in line:
                key, value = line.split(':', 1)
                result[key.strip()] = value.strip()
        return result
        
    def _parse_cascade_rules(self, section: str) -> Dict[str, Any]:
        """Parse cascade rules"""
        rules = {}
        for line in section.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('- '):
                line = line[2:]
            
            # Format: "condition: action"
            if ':' in line:
                condition, action = line.split(':', 1)
                rules[condition.strip()] = action.strip()
                
        return rules
        
    def _parse_skill_routes(self, section: str) -> Dict[str, List[str]]:
        """Parse skill routing configuration"""
        routes = {}
        for line in section.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Format: "skill: [dep1, dep2, dep3]"
            if ':' in line:
                skill, deps = line.split(':', 1)
                skill = skill.strip()
                
                # Parse dependencies (either [a,b,c] or comma-separated)
                deps_str = deps.strip()
                if deps_str.startswith('[') and deps_str.endswith(']'):
                    deps_str = deps_str[1:-1]
                    
                deps_list = [d.strip().strip('"\'') for d in deps_str.split(',')]
                routes[skill] = deps_list
                
        return routes
        
    def _parse_evolution_suggestions(self, section: str) -> List[Dict[str, str]]:
        """Parse evolution suggestions"""
        suggestions = []
        for line in section.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('- '):
                line = line[2:]
                
            # Format: "[PRIORITY] description → action"
            match = re.match(r'\[(CRITICAL|HIGH|MEDIUM|LOW)\]\s+(.*?)\s*→\s*(.*)', line)
            if match:
                suggestions.append({
                    'priority': match.group(1),
                    'description': match.group(2),
                    'action': match.group(3)
                })
                
        return suggestions
        
    def get_model_for_skill(self, skill_name: str) -> Optional[str]:
        """Get model assignment for a skill"""
        if not self._account_config:
            self.load_config()
            
        return self._account_config.get('model_assignments', {}).get(skill_name)
        
    def get_cascade_rules(self) -> Dict[str, Any]:
        """Get all cascade rules"""
        if not self._account_config:
            self.load_config()
            
        return self._account_config.get('cascade_rules', {})
        
    def get_evolution_suggestions(self, priority: Optional[str] = None) -> List[Dict[str, str]]:
        """Get evolution suggestions, optionally filtered by priority"""
        if not self._account_config:
            self.load_config()
            
        suggestions = self._account_config.get('evolution_suggestions', [])
        
        if priority:
            suggestions = [s for s in suggestions if s.get('priority') == priority]
            
        return suggestions
        
    def apply_cascade_rule(self, condition: str) -> Optional[str]:
        """Check if condition matches cascade rule and return action"""
        rules = self.get_cascade_rules()
        
        for rule_condition, action in rules.items():
            if self._eval_condition(condition, rule_condition):
                return action
                
        return None
        
    def _eval_condition(self, actual: str, rule: str) -> bool:
        """Simple condition evaluation"""
        # Very basic matching - real implementation would use proper expression parsing
        if rule.lower() in actual.lower():
            return True
        return False
        
    def format_config_summary(self) -> str:
        """Format configuration for display"""
        if not self._account_config:
            self.load_config()
            
        lines = []
        lines.append("⚙️ Configuration Summary")
        lines.append(f"   Source: {self._account_config.get('path', 'not loaded')}")
        
        models = self._account_config.get('model_assignments', {})
        if models:
            lines.append(f"   Models: {len(models)} configured")
            
        cascades = self._account_config.get('cascade_rules', {})
        if cascades:
            lines.append(f"   Cascades: {len(cascades)} rules")
            
        suggestions = self._account_config.get('evolution_suggestions', [])
        if suggestions:
            critical = len([s for s in suggestions if s.get('priority') == 'CRITICAL'])
            if critical:
                lines.append(f"   ⚠️ {critical} CRITICAL suggestions")
                
        return "\n".join(lines)
