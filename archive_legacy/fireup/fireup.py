"""
Fireup - Dynamic startup and skill management for JARVIS.

Key Features:
1. Auto-detects workspace type and loads appropriate skills
2. Updates itself based on new folders/files
3. Integrates with MCP for autonomous intelligence
4. Syncs with persona system for personalized operation
5. Supports hot-reload of skills without restart
"""

import asyncio
import importlib
import inspect
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Type
from dataclasses import dataclass, asdict
from datetime import datetime

from utils.logger import get_logger
from utils.config import Config
from utils.event_bus import EventBus, Event, EventType
from persona.persona_manager import PersonaManager
from scanner.workspace_scanner import WorkspaceScanner, WorkspaceProfile

logger = get_logger(__name__)


@dataclass
class SkillMetadata:
    """Metadata about a skill"""
    name: str
    module: str
    class_name: str
    description: str
    applicable_tech: List[str]
    priority: int = 1  # 1=high, 5=low
    dependencies: List[str] = None
    auto_load: bool = False  # If True, loads automatically when tech detected
    version: str = "1.0.0"
    author: str = ""
    tags: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.tags is None:
            self.tags = []


class SkillRegistry:
    """Registry of all available skills"""
    
    def __init__(self, skills_dir: Path = Path("mcp/skills")):
        self.skills_dir = skills_dir
        self.skills: Dict[str, SkillMetadata] = {}
        self.loaded_instances: Dict[str, Any] = {}
        self._scan_skills()
    
    def _scan_skills(self):
        """Scan skills directory and build registry"""
        if not self.skills_dir.exists():
            logger.warning(f"Skills directory does not exist: {self.skills_dir}")
            return
        
        # Find all Python files in skills directory
        skill_files = list(self.skills_dir.glob("*.py"))
        
        for skill_file in skill_files:
            if skill_file.name.startswith("_"):
                continue  # Skip __init__.py and private files
            
            module_name = f"mcp.skills.{skill_file.stem}"
            
            try:
                # Import module
                module = importlib.import_module(module_name)
                
                # Find skill classes (subclasses of BaseSkill)
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and hasattr(obj, '__bases__'):
                        # Check if it's a skill (has required attributes)
                        if hasattr(obj, 'name') and hasattr(obj, 'description'):
                            metadata = SkillMetadata(
                                name=getattr(obj, 'name', obj.__name__.lower()),
                                module=module_name,
                                class_name=name,
                                description=getattr(obj, 'description', ''),
                                applicable_tech=getattr(obj, 'applicable_tech', []),
                                priority=getattr(obj, 'priority', 1),
                                dependencies=getattr(obj, 'dependencies', []),
                                auto_load=getattr(obj, 'auto_load', False),
                                version=getattr(obj, 'version', '1.0.0'),
                                author=getattr(obj, 'author', ''),
                                tags=getattr(obj, 'tags', [])
                            )
                            self.skills[metadata.name] = metadata
                            logger.debug(f"Registered skill: {metadata.name}")
            except Exception as e:
                logger.error(f"Failed to import skill module {module_name}: {e}")
    
    def get_skills_for_tech(self, tech_stack: List[str]) -> List[SkillMetadata]:
        """Get all skills applicable to given tech stack"""
        applicable = []
        for skill in self.skills.values():
            # Check if any of skill's applicable tech matches
            if any(tech in skill.applicable_tech for tech in tech_stack):
                applicable.append(skill)
        
        # Sort by priority
        applicable.sort(key=lambda s: s.priority)
        return applicable
    
    def get_skill(self, name: str) -> Optional[SkillMetadata]:
        """Get skill metadata by name"""
        return self.skills.get(name)
    
    def list_skills(self) -> List[SkillMetadata]:
        """List all available skills"""
        return list(self.skills.values())
    
    async def load_skill(self, skill_name: str, context: Dict[str, Any] = None) -> Any:
        """Instantiate a skill by name"""
        if skill_name in self.loaded_instances:
            return self.loaded_instances[skill_name]
        
        metadata = self.skills.get(skill_name)
        if not metadata:
            raise ValueError(f"Skill not found: {skill_name}")
        
        try:
            module = importlib.import_module(metadata.module)
            skill_class = getattr(module, metadata.class_name)
            
            # Instantiate with context if needed
            if context:
                instance = skill_class(**context)
            else:
                instance = skill_class()
            
            self.loaded_instances[skill_name] = instance
            logger.info(f"Loaded skill: {skill_name}")
            return instance
        except Exception as e:
            logger.error(f"Failed to load skill {skill_name}: {e}")
            raise
    
    def unload_skill(self, skill_name: str):
        """Unload a skill from memory"""
        if skill_name in self.loaded_instances:
            del self.loaded_instances[skill_name]
            logger.info(f"Unloaded skill: {skill_name}")
    
    def get_skill_effectiveness(self, persona_id: str, skill_name: str) -> float:
        """Get effectiveness score for skill with persona"""
        # Load from history DB
        # For now, return base priority converted to 0-1 scale
        metadata = self.skills.get(skill_name)
        if metadata:
            return 1.0 / metadata.priority  # Lower priority number = higher score
        return 0.5
    
    def save_registry(self, path: Path):
        """Save registry to JSON"""
        data = {
            name: asdict(metadata)
            for name, metadata in self.skills.items()
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_registry(self, path: Path):
        """Load registry from JSON"""
        if not path.exists():
            return
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        # Reconstruct SkillMetadata objects
        self.skills = {}
        for name, metadata_dict in data.items():
            metadata = SkillMetadata(**metadata_dict)
            self.skills[name] = metadata


class Fireup:
    """
    Dynamic startup manager that adapts to workspace and persona.
    
    Features:
    - Auto-detects workspace technology stack
    - Loads appropriate skills based on tech + persona
    - Updates configuration based on scanner output
    - Supports hot-reload when new files/folders added
    - Integrates with MCP for context awareness
    """
    
    def __init__(self, config: Config, event_bus: EventBus, 
                 persona_manager: PersonaManager, registry: SkillRegistry):
        self.config = config
        self.event_bus = event_bus
        self.persona_manager = persona_manager
        self.registry = registry
        self.workspace_scanner = WorkspaceScanner()
        
        self.current_workspace: Optional[Path] = None
        self.current_profile: Optional[WorkspaceProfile] = None
        self.current_persona = None
        self.loaded_skills: List[str] = []
        
        # Configuration paths
        self.fireup_config_path = Path("fireup_config.json")
        self.dynamic_skills_path = Path("fireup/dynamic_skills/auto_generated.py")
        
        # Subscribe to events
        self._subscribe_to_events()
        
        logger.info("Fireup initialized")
    
    def _subscribe_to_events(self):
        """Subscribe to relevant events"""
        self.event_bus.subscribe(
            "fireup",
            [EventType.NEW_WORKSPACE, EventType.FILE_CREATED, EventType.FOLDER_CREATED],
            self._handle_workspace_change
        )
        
        self.event_bus.subscribe(
            "fireup",
            [EventType.PERSONA_SWITCHED],
            self._handle_persona_switch
        )
    
    async def initialize(self, workspace_path: Optional[Path] = None):
        """
        Initialize fireup for a workspace.
        
        Args:
            workspace_path: Path to workspace. If None, uses current directory.
        """
        if workspace_path is None:
            workspace_path = Path.cwd()
        
        self.current_workspace = workspace_path.resolve()
        logger.info(f"Initializing fireup for workspace: {self.current_workspace}")
        
        # 1. Detect current persona
        self.current_persona = self.persona_manager.get_persona_for_workspace(self.current_workspace)
        if not self.current_persona:
            logger.warning(f"No persona found for workspace {self.current_workspace}, using default")
            self.current_persona = self.persona_manager.get_default_persona()
        
        logger.info(f"Active persona: {self.current_persona.name}")
        
        # 2. Scan workspace to build profile
        logger.info("Scanning workspace...")
        self.current_profile = await self.workspace_scanner.scan(self.current_workspace)
        
        # 3. Determine required skills
        required_skills = self._determine_required_skills(self.current_profile, self.current_persona)
        
        # 4. Load skills
        await self._load_skills(required_skills)
        
        # 5. Update fireup configuration
        self._update_fireup_config()
        
        # 6. Notify system
        await self.event_bus.publish(Event(
            type=EventType.NEW_WORKSPACE,
            source="fireup.initialize",
            timestamp=datetime.utcnow(),
            data={
                "workspace": str(self.current_workspace),
                "persona": self.current_persona.id,
                "profile": self.current_profile.to_dict(),
                "skills_loaded": self.loaded_skills
            }
        ))
        
        logger.info(f"Fireup initialized: {len(self.loaded_skills)} skills loaded")
    
    def _determine_required_skills(self, profile: WorkspaceProfile, persona) -> List[str]:
        """
        Determine which skills should be loaded based on workspace profile and persona.
        
        Logic:
        1. Base: Always load core skills (file_modder, code_generator, etc.)
        2. Tech-based: Load skills for detected tech stack
        3. Persona-based: Load persona's preferred skills
        4. Pattern-based: Load skills for common patterns in workspace
        5. Context-based: Load skills based on recent activity
        """
        required = set()
        
        # 1. Always include core skills
        core_skills = ["file_modder", "code_generator", "config_updater"]
        required.update(core_skills)
        
        # 2. Tech-based skills
        for tech in profile.tech_stack:
            tech_skills = self.registry.get_skills_for_tech([tech])
            for skill in tech_skills:
                if skill.auto_load:  # Only auto-load if marked
                    required.add(skill.name)
        
        # 3. Persona preferences
        if hasattr(persona, 'preferences') and hasattr(persona.preferences, 'skills'):
            required.update(persona.preferences.skills)
        
        # 4. Pattern-based (from learned patterns)
        if profile.common_patterns:
            for pattern in profile.common_patterns:
                # Map pattern to skill
                skill_name = self._pattern_to_skill(pattern)
                if skill_name:
                    required.add(skill_name)
        
        # 5. Context from recent events
        # (To be implemented based on conversation or task context)
        
        # Deduplicate and sort by priority
        skills_list = list(required)
        skills_list.sort(key=lambda s: self.registry.get_skill(s).priority if self.registry.get_skill(s) else 999)
        
        return skills_list
    
    def _pattern_to_skill(self, pattern: str) -> Optional[str]:
        """Map a learned pattern to a skill name"""
        pattern_skill_map = {
            "django_model": "django_skills",
            "react_component": "react_skills",
            "api_endpoint": "fastapi_skills",
            "docker": "docker_skills",
            "kubernetes": "kubernetes_skills",
            "test_": "testing_skills",
            "fixture": "testing_skills",
            "mock": "testing_skills",
            "deploy": "deployment_skills",
            "ci": "ci_cd_skills",
            "migration": "database_migration_skills",
            "refactor": "refactoring_skills",
            "optimization": "performance_skills",
            "security": "security_skills",
        }
        
        for pattern_key, skill_name in pattern_skill_map.items():
            if pattern_key in pattern.lower():
                return skill_name
        
        return None
    
    async def _load_skills(self, skill_names: List[str]):
        """Load the specified skills"""
        loaded = []
        
        for skill_name in skill_names:
            try:
                await self.registry.load_skill(skill_name)
                loaded.append(skill_name)
            except Exception as e:
                logger.error(f"Failed to load skill {skill_name}: {e}")
        
        self.loaded_skills = loaded
        logger.info(f"Successfully loaded {len(loaded)} skills: {', '.join(loaded)}")
    
    def _update_fireup_config(self):
        """Update fireup configuration file"""
        config = {
            "workspace": str(self.current_workspace),
            "persona": self.current_persona.id if self.current_persona else None,
            "profile": self.current_profile.to_dict() if self.current_profile else None,
            "loaded_skills": self.loaded_skills,
            "last_updated": datetime.utcnow().isoformat(),
            "version": "2.0"
        }
        
        with open(self.fireup_config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Also generate dynamic skills file
        self._generate_dynamic_skills_file()
        
        logger.debug(f"Updated fireup config: {self.fireup_config_path}")
    
    def _generate_dynamic_skills_file(self):
        """Generate auto_generated.py with workspace-specific skills based on patterns"""
        if not self.current_profile or not self.current_profile.common_patterns:
            return
        
        # Create directory if needed
        self.dynamic_skills_path.parent.mkdir(parents=True, exist_ok=True)
        
        content = '''"""
Auto-generated skills for workspace based on learned patterns.
Generated by JARVIS Fireup on {timestamp}

DO NOT EDIT MANUALLY - This file is auto-generated.
Your edits will be overwritten.
"""

from mcp.skills.base_skill import BaseSkill


class WorkspaceSpecificSkills:
    """Collection of skills generated from workspace patterns"""
    
    workspace = "{workspace}"
    patterns = {patterns}
    
    @staticmethod
    def get_skill_for_pattern(pattern: str):
        """Get skill class for a specific pattern"""
        skill_map = {{
{skill_map}
        }}
        return skill_map.get(pattern)
'''
        
        # Map patterns to skill classes
        skill_map = {}
        for pattern in self.current_profile.common_patterns[:10]:  # Top 10
            skill_name = self._pattern_to_skill(pattern)
            if skill_name:
                skill_map[pattern] = f"{skill_name}.{skill_name.title()}Skill"
        
        formatted_content = content.format(
            timestamp=datetime.utcnow().isoformat(),
            workspace=str(self.current_workspace),
            patterns=json.dumps(self.current_profile.common_patterns, indent=12),
            skill_map=",\n".join([f'            "{k}": {v}' for k, v in skill_map.items()])
        )
        
        with open(self.dynamic_skills_path, 'w') as f:
            f.write(formatted_content)
        
        logger.info(f"Generated dynamic skills file: {self.dynamic_skills_path}")
    
    async def reload_for_workspace_change(self, change_event: Event):
        """
        Handle workspace change (new file/folder) and reload skills if needed.
        
        This is the key to dynamic adaptation!
        """
        logger.info(f"Workspace change detected: {change_event.data}")
        
        # Re-scan workspace (or just the changed path)
        # For now, re-scan entire workspace
        new_profile = await self.workspace_scanner.scan(self.current_workspace)
        
        # Check if tech stack changed
        old_tech = set(self.current_profile.tech_stack)
        new_tech = set(new_profile.tech_stack)
        
        tech_changed = old_tech != new_tech
        
        # Check if patterns changed
        old_patterns = set(self.current_profile.common_patterns)
        new_patterns = set(new_profile.common_patterns)
        patterns_changed = old_patterns != new_patterns
        
        if tech_changed or patterns_changed:
            logger.info("Workspace profile changed, updating skills...")
            
            # Update profile
            self.current_profile = new_profile
            
            # Re-determine required skills
            required_skills = self._determine_required_skills(self.current_profile, self.current_persona)
            current_set = set(self.loaded_skills)
            required_set = set(required_skills)
            
            # Skills to add
            to_add = required_set - current_set
            # Skills to remove (if any, though usually we keep)
            to_remove = current_set - required_set
            
            if to_add:
                logger.info(f"Adding skills: {to_add}")
                await self._load_skills(list(to_add))
            
            if to_remove:
                logger.info(f"Removing skills: {to_remove}")
                for skill in to_remove:
                    self.registry.unload_skill(skill)
                self.loaded_skills = [s for s in self.loaded_skills if s not in to_remove]
            
            # Update config
            self._update_fireup_config()
            
            logger.info(f"Skills updated. Now loaded: {len(self.loaded_skills)} skills")
        else:
            logger.debug("Workspace change doesn't require skill update")
    
    async def _handle_workspace_change(self, event: Event):
        """Handle workspace change event"""
        if event.type in [EventType.FILE_CREATED, EventType.FOLDER_CREATED, EventType.NEW_WORKSPACE]:
            await self.reload_for_workspace_change(event)
    
    async def _handle_persona_switch(self, event: Event):
        """Handle persona switch event"""
        new_persona_id = event.data.get("persona_id")
        if new_persona_id:
            self.current_persona = self.persona_manager.get_persona(new_persona_id)
            if self.current_persona:
                logger.info(f"Switched to persona: {self.current_persona.name}")
                # Re-evaluate skills with new persona
                if self.current_profile:
                    required_skills = self._determine_required_skills(self.current_profile, self.current_persona)
                    await self._load_skills(required_skills)
                    self._update_fireup_config()
    
    def get_loaded_skill_instances(self) -> Dict[str, Any]:
        """Get dictionary of loaded skill instances"""
        return {
            name: self.registry.loaded_instances.get(name)
            for name in self.loaded_skills
            if name in self.registry.loaded_instances
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get fireup status"""
        return {
            "workspace": str(self.current_workspace) if self.current_workspace else None,
            "persona": self.current_persona.id if self.current_persona else None,
            "profile_scan_time": self.current_profile.scan_timestamp.isoformat() if self.current_profile else None,
            "tech_stack": self.current_profile.tech_stack if self.current_profile else [],
            "loaded_skills": self.loaded_skills,
            "total_skills_available": len(self.registry.skills),
            "fireup_config": self.fireup_config_path.exists()
        }


async def create_fireup(config: Config, event_bus: EventBus, 
                      persona_manager: PersonaManager) -> Fireup:
    """
    Factory function to create and initialize Fireup.
    
    Args:
        config: System configuration
        event_bus: Event bus instance
        persona_manager: Persona manager instance
        
    Returns:
        Initialized Fireup instance
    """
    # Create skill registry
    skills_dir = Path(config.root_dir) / "mcp" / "skills"
    registry = SkillRegistry(skills_dir)
    
    # Load saved registry if exists
    registry_path = Path(config.data_dir) / "skills" / "skill_registry.json"
    if registry_path.exists():
        registry.load_registry(registry_path)
    
    # Create fireup
    fireup = Fireup(config, event_bus, persona_manager, registry)
    
    # Initialize with workspace from config or current directory
    workspace_path = None
    if config.workspace_paths:
        workspace_path = Path(config.workspace_paths[0])
    
    await fireup.initialize(workspace_path)
    
    return fireup


# Example usage:
# async def main():
#     config = Config.load()
#     event_bus = EventBus()
#     persona_manager = PersonaManager()
#     fireup = await create_fireup(config, event_bus, persona_manager)
#     print(f"Loaded skills: {fireup.loaded_skills}")
