#!/usr/bin/env python3
"""Pattern Recognition Learner - discovers coding patterns and preferences."""

import json
from pathlib import Path
from typing import Dict, Any, List
from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event
from jarvis.utils.config import ConfigManager


class PatternRecognition:
    """Learns and stores code patterns, user preferences, and domain knowledge."""

    def __init__(self, config, event_bus: EventBus):
        self.config = config
        self.event_bus = event_bus
        self.logger = JARVISLogger("pattern_recognition")
        self.patterns_dir = config.patterns_dir
        self.patterns_dir.mkdir(parents=True, exist_ok=True)
        self.patterns_file = self.patterns_dir / "patterns.json"
        self.patterns: Dict[str, Any] = self._load_patterns()

        # Subscribe to events
        self.event_bus.subscribe("conversation.message", self._on_conversation)
        self.event_bus.subscribe("file.created", self._on_file_created)
        self.event_bus.subscribe("file.modified", self._on_file_modified)

    def _load_patterns(self) -> Dict[str, Any]:
        """Load existing patterns from disk."""
        if self.patterns_file.exists():
            with open(self.patterns_file) as f:
                return json.load(f)
        return {
            "code_patterns": {},
            "preferences": {},
            "domain_concepts": [],
            "skills_used": [],
            "statistics": {
                "total_files_observed": 0,
                "total_edits_observed": 0,
                "patterns_discovered": 0
            }
        }

    def _save_patterns(self):
        """Save patterns to disk with backup."""
        backup = self.patterns_file.with_suffix('.json.bak')
        if self.patterns_file.exists():
            self.patterns_file.rename(backup)
        with open(self.patterns_file, 'w') as f:
            json.dump(self.patterns, f, indent=2)
        if backup.exists():
            backup.unlink()  # Remove backup after successful write

    async def start(self):
        """Start pattern recognition."""
        self.logger.info("Pattern recognition started", patterns_count=len(self.patterns))

    async def stop(self):
        """Stop and save."""
        self._save_patterns()
        self.logger.info("Pattern recognition stopped")

    # Event handlers
    def _on_conversation(self, event: Event):
        """Extract patterns from conversation."""
        content = event.data.get("content", "")
        if not content:
            return

        # Simple keyword-based preference extraction
        # In real implementation, use LLM embeddings
        preferences = {
            "ruthless": "communication_style" in content.lower(),
            "no_bs": "zero tolerance" in content.lower(),
            "ai_enthusiast": any(k in content.lower() for k in ["openai", "claude", "gpt", "llm"]),
            "saas_builder": "saas" in content.lower(),
        }

        for pref, present in preferences.items():
            if present:
                current = self.patterns["preferences"].get(pref, 0)
                self.patterns["preferences"][pref] = current + 1

        # Detect skills mentioned
        skills = ["battlecards", "demo_strategy", "meddpicc", "value_architecture", "risk_report"]
        for skill in skills:
            if skill.replace('_', ' ') in content.lower():
                if skill not in self.patterns["skills_used"]:
                    self.patterns["skills_used"].append(skill)

    def _on_file_created(self, event: Event):
        path = event.data.get("path", "")
        if path.endswith(".py"):
            self.patterns["statistics"]["total_files_observed"] += 1
            self._infer_framework(path)

    def _on_file_modified(self, event: Event):
        self.patterns["statistics"]["total_edits_observed"] += 1

    def _infer_framework(self, filepath: str):
        """Very basic framework detection."""
        try:
            with open(filepath) as f:
                content = f.read(4096)  # read first 4KB
            frameworks = []
            if "from django" in content or "from rest_framework" in content:
                frameworks.append("django")
            if "from fastapi" in content:
                frameworks.append("fastapi")
            if "import flask" in content:
                frameworks.append("flask")
            if "from flask" in content:
                frameworks.append("flask")
            if "from tornado" in content:
                frameworks.append("tornado")
            if "React.createClass" in content or "from 'react'" in content:
                frameworks.append("react")

            for fw in frameworks:
                if fw not in self.patterns["code_patterns"]:
                    self.patterns["code_patterns"][fw] = {"files": 0, "imports": []}
                self.patterns["code_patterns"][fw]["files"] += 1
        except:
            pass  # ignore read errors