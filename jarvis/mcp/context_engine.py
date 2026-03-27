#!/usr/bin/env python3
"""Context Engine - maintains semantic context for the current workspace and persona."""

import json
from pathlib import Path
from typing import Dict, Any, List
from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event


class ContextEngine:
    """Provides contextual awareness for MCP operations."""

    def __init__(self, config, event_bus: EventBus):
        self.config = config
        self.event_bus = event_bus
        self.logger = JARVISLogger("context_engine")
        self.context_file = config.cache_dir / "context.json"
        self.context: Dict[str, Any] = self._load_context()
        self._current_workspace: str = ""
        self._current_persona: str = ""

        self.event_bus.subscribe("workspace.scanned", self._on_workspace_scanned)
        self.event_bus.subscribe("persona.switched", self._on_persona_switched)
        self.event_bus.subscribe("conversation.message", self._update_from_conversation)

    def _load_context(self) -> Dict[str, Any]:
        if self.context_file.exists():
            with open(self.context_file) as f:
                return json.load(f)
        return {
            "current_workspace": "",
            "current_persona": "",
            "project_type": "",
            "frameworks": [],
            "recent_files": [],
            "domain_terms": [],
            "last_updated": ""
        }

    def _save_context(self):
        self.context_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.context_file, 'w') as f:
            json.dump(self.context, f, indent=2)

    def _on_workspace_scanned(self, event: Event):
        workspace = event.data.get("workspace", "")
        project_type = event.data.get("project_type", "unknown")
        self.context["current_workspace"] = workspace
        self.context["project_type"] = project_type
        self._current_workspace = workspace
        self._save_context()
        self.logger.info("Context updated", workspace=workspace, project_type=project_type)

    def _on_persona_switched(self, event: Event):
        persona = event.data.get("to", "")
        self.context["current_persona"] = persona
        self._current_persona = persona
        self._save_context()
        self.logger.info("Context persona updated", persona=persona)

    def _update_from_conversation(self, event: Event):
        content = event.data.get("content", "")
        if self._current_workspace in content:
            # Mention of current workspace context
            pass  # Could extract new domain terms

    def get_context(self) -> Dict[str, Any]:
        """Get current context snapshot."""
        return self.context.copy()

    def get_recent_files(self, limit: int = 10) -> List[str]:
        """Get recently mentioned files."""
        return self.context.get("recent_files", [])[-limit:]

    def get_frameworks(self) -> List[str]:
        """Get detected frameworks for current workspace."""
        return self.context.get("frameworks", [])

    async def start(self):
        self.logger.info("Context engine started")

    async def stop(self):
        self._save_context()
        self.logger.info("Context engine stopped")