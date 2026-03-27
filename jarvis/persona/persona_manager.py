#!/usr/bin/env python3
"""
Persona Manager - Handles multiple personas with isolated contexts.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event


@dataclass
class Persona:
    """Represents a user persona with its own preferences and workspace mappings."""
    id: str
    name: str
    persona_type: str  # solution_consultant, account_executive, etc.
    workspaces: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    deals: List[Dict[str, Any]] = field(default_factory=list)
    knowledge_graph: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    last_active: Optional[str] = None


class PersonaManager:
    """Manages multiple personas and handles switching."""

    def __init__(self, config, event_bus: EventBus):
        self.config = config
        self.event_bus = event_bus
        self.logger = JARVISLogger("persona_manager")
        self.personas_dir = config.personas_dir
        self.personas_dir.mkdir(parents=True, exist_ok=True)
        self.personas_file = self.personas_dir / "personas.json"
        self.active_persona: Optional[Persona] = None
        self.personas: Dict[str, Persona] = {}

        # History DB
        self.history_db_path = config.history_db_path
        self._init_history_db()

    def _init_history_db(self):
        """Initialize SQLite database for persona history."""
        self.history_db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.history_db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS persona_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                persona_id TEXT NOT NULL,
                component TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS deals (
                deal_id TEXT PRIMARY KEY,
                persona_id TEXT NOT NULL,
                title TEXT NOT NULL,
                client TEXT,
                deadline DATETIME,
                status TEXT,
                budget REAL,
                tasks_completed INTEGER DEFAULT 0,
                total_tasks INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (persona_id) REFERENCES personas (id)
            )
        """)
        conn.commit()
        conn.close()

    async def start(self):
        """Load existing personas and set default."""
        self.logger.info("Starting persona manager")
        self._load_personas()

        # Load default persona
        default_id = self.config.default_persona
        if default_id in self.personas:
            await self.switch_persona(default_id)
        else:
            # Create a default persona if none exists
            await self.create_persona("work", "work", "solution_consultant")

        # Subscribe to persona-related events
        self.event_bus.subscribe("workspace.scanned", self._on_workspace_scanned)

    def _load_personas(self):
        """Load all personas from disk."""
        if self.personas_file.exists():
            with open(self.personas_file) as f:
                data = json.load(f)
                for pdata in data.get("personas", []):
                    persona = Persona(**pdata)
                    self.personas[persona.id] = persona
            self.logger.info("Loaded personas", count=len(self.personas))
        else:
            self._save_personas()

    def _save_personas(self):
        """Save all personas to disk."""
        data = {
            "personas": [asdict(p) for p in self.personas.values()],
            "last_updated": self._now_iso()
        }
        with open(self.personas_file, 'w') as f:
            json.dump(data, f, indent=2)

    async def create_persona(self, persona_id: str, name: str, persona_type: str,
                             workspaces: list[str] = None) -> Persona:
        """Create a new persona."""
        if persona_id in self.personas:
            raise ValueError(f"Persona {persona_id} already exists")

        persona = Persona(
            id=persona_id,
            name=name,
            persona_type=persona_type,
            workspaces=workspaces or []
        )
        self.personas[persona_id] = persona
        self._save_personas()
        self.logger.info("Created persona", id=persona_id, name=name, type=persona_type)

        # Log to history
        self._log_activity(persona_id, "persona_manager", "created", {"name": name})
        return persona

    async def switch_persona(self, persona_id: str) -> bool:
        """Switch active persona."""
        if persona_id not in self.personas:
            self.logger.error("Persona not found", persona_id=persona_id)
            return False

        old = self.active_persona.id if self.active_persona else None
        self.active_persona = self.personas[persona_id]
        self.active_persona.last_active = self._now_iso()
        self._save_personas()

        self.logger.info("Persona switched", from_=old, to=persona_id)
        self.event_bus.publish(Event("persona.switched", "persona_manager", {
            "from": old, "to": persona_id, "type": self.active_persona.persona_type
        }))
        return True

    def get_active_persona(self) -> Optional[Persona]:
        """Get currently active persona."""
        return self.active_persona

    def list_personas(self) -> list[Dict[str, Any]]:
        """List all personas with basic info."""
        return [
            {
                "id": p.id,
                "name": p.name,
                "type": p.persona_type,
                "workspaces": p.workspaces,
                "deals_count": len(p.deals),
                "last_active": p.last_active
            }
            for p in self.personas.values()
        ]

    async def add_workspace(self, persona_id: str, workspace_path: str) -> bool:
        """Add a workspace to a persona."""
        if persona_id not in self.personas:
            return False
        if workspace_path not in self.personas[persona_id].workspaces:
            self.personas[persona_id].workspaces.append(workspace_path)
            self._save_personas()
            self.logger.info("Workspace added", persona=persona_id, workspace=workspace_path)
        return True

    # Deal management
    async def create_deal(self, persona_id: str, title: str, client: str = None,
                          deadline: str = None, budget: float = None) -> str:
        """Create a new deal for a persona."""
        if persona_id not in self.personas:
            raise ValueError(f"Persona {persona_id} not found")

        deal_id = f"deal_{self._now_timestamp()}"
        deal = {
            "deal_id": deal_id,
            "persona_id": persona_id,
            "title": title,
            "client": client,
            "deadline": deadline,
            "budget": budget,
            "status": "open",
            "tasks_completed": 0,
            "total_tasks": 0,
            "created_at": self._now_iso()
        }

        self.personas[persona_id].deals.append(deal)
        self._save_personas()

        # Insert into history DB
        conn = sqlite3.connect(self.history_db_path)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO deals (deal_id, persona_id, title, client, deadline, status, budget)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (deal_id, persona_id, title, client, deadline, "open", budget))
        conn.commit()
        conn.close()

        self.logger.info("Deal created", deal_id=deal_id, persona=persona_id, title=title)
        self._log_activity(persona_id, "deal", "created", {"deal_id": deal_id, "title": title})

        return deal_id

    def list_deals(self, persona_id: str = None) -> list[Dict]:
        """List deals, optionally filtered by persona."""
        if persona_id:
            return self.personas.get(persona_id, {}).deals
        deals = []
        for p in self.personas.values():
            deals.extend(p.deals)
        return deals

    # History logging
    def _log_activity(self, persona_id: str, component: str, action: str, details: Dict = None):
        """Log activity to history database."""
        conn = sqlite3.connect(self.history_db_path)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO persona_activity (persona_id, component, action, details)
            VALUES (?, ?, ?, ?)
        """, (
            persona_id,
            component,
            action,
            json.dumps(details) if details else None
        ))
        conn.commit()
        conn.close()

    # Event handlers
    def _on_workspace_scanned(self, event: Event):
        """Handle workspace scan completion."""
        workspace = event.data.get("workspace")
        project_type = event.data.get("project_type")

        # Auto-assign workspace to persona based on matching logic
        for persona in self.personas.values():
            for ws in persona.workspaces:
                if workspace.startswith(ws) or ws.startswith(workspace):
                    self.logger.debug("Workspace matched persona",
                                      workspace=workspace, persona=persona.id)
                    # Could auto-switch persona here based on config.auto_persona_switch
                    break

    def _now_iso(self) -> str:
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"

    def _now_timestamp(self) -> str:
        import time
        return str(int(time.time()))

    async def stop(self):
        """Stop persona manager."""
        self.logger.info("Persona manager stopped")
