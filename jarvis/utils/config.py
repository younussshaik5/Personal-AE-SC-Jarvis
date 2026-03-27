#!/usr/bin/env python3
"""
Configuration management for JARVIS with schema validation and hot reload.
"""

import os
import yaml
import json
import asyncio
from pathlib import Path
from typing import Any, Dict, Optional, List, Callable
from dataclasses import dataclass, field, asdict


@dataclass
class JarvisConfig:
    """Main configuration container."""

    # Core
    workspace_root: Path = Path.cwd() / "OPENCODE SPACE"
    data_dir: Path = Path.cwd() / "data"
    logs_dir: Path = Path.cwd() / "logs"
    temp_dir: Path = Path.cwd() / "tmp"

    # MCP / OpenCode integration
    opencode_db_path: Path = Path.home() / ".local/share/opencode/opencode.db"
    opencode_api_url: str = "http://localhost:4096"
    mcp_server_enabled: bool = True
    mcp_transport: str = "stdio"  # stdio, websocket, http

    # Safety
    approval_required: bool = True
    approval_threshold: int = 50  # number of auto-approvals before threshold
    killswitch_path: Path = Path(".jarvis.killswitch")
    backup_retention_days: int = 90
    max_rollback_chain: int = 100

    # Evolution
    evolution_enabled: bool = True
    evolution_interval_hours: int = 6
    max_improvements_per_cycle: int = 3
    ab_test_duration_hours: int = 24
    require_ab_test: bool = True

    # Observers
    observe_filesystem: bool = True
    observe_git: bool = True
    observe_conversations: bool = True
    observe_database: bool = True
    polling_interval_seconds: int = 10

    # Archiving
    archiving_enabled: bool = True
    daily_snapshot: bool = True
    weekly_full_snapshot: bool = True
    archive_compression: str = "gzip"  # gzip, zip, none

    # Logging
    log_level: str = "INFO"
    log_json: bool = True
    log_retention_days: int = 30

    # Performance
    max_concurrent_updates: int = 5
    embedding_cache_size: int = 1000
    max_memory_mb: int = 1024

    # Persona
    default_persona: str = "work"
    auto_persona_switch: bool = True
    persona_trust_threshold: float = 0.5

    # Telegram notifications
    telegram: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": False,
        "bot_token": "",
        "allowed_user_ids": [],  # List of Telegram user IDs allowed to chat
        "channel_id": "",
        "broadcast_events": True,
        "allow_conversational_chat": True,
        "allow_commands": True,
        "notify_on_persona_switch": True,
        "notify_on_modification_approved": True,
        "notify_on_pattern_discovered": False,
        "notify_on_competitor_detected": True,
        "notify_on_errors": True,
        "rate_limit_per_minute": 10
    })

    # LLM configuration for natural conversation
    llm: Dict[str, Any] = field(default_factory=lambda: {
        "provider": "openai",  # openai, anthropic, nvidia, local, mock
        "api_key": "",  # Your API key (or set NVIDIA_API_KEY env var)
        "base_url": "https://integrate.api.nvidia.com/v1",  # NVIDIA endpoint
        "model": "stepfun-ai/step-3.5-flash",  # Model identifier
        "temperature": 1,
        "top_p": 0.9,
        "max_tokens": 16384,
        "context_window": 32768,
        "extra_body": None,  # No extra body needed for this model
        "stream": False
    })

    # OpenCode AI integration: use OpenCode's configured AI instead of local
    opencode_ai_enabled: bool = False
    opencode_ai_config_path: str = "~/.config/opencode/config.yaml"

    # Paths (computed)
    @property
    def personas_dir(self) -> Path:
        return self.data_dir / "personas"

    @property
    def patterns_dir(self) -> Path:
        return self.data_dir / "patterns"

    @property
    def skills_dir(self) -> Path:
        return self.data_dir / "skills"

    @property
    def archives_dir(self) -> Path:
        return self.data_dir / "archives"

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"

    @property
    def history_db_path(self) -> Path:
        return self.data_dir / "history" / "jarvis.db"

    def ensure_dirs(self):
        """Create necessary directories."""
        for path_attr in [
            'workspace_root', 'data_dir', 'logs_dir', 'temp_dir',
            'personas_dir', 'patterns_dir', 'skills_dir',
            'archives_dir', 'cache_dir', 'history_db_path'
        ]:
            path = getattr(self, path_attr)
            if isinstance(path, Path):
                path.parent.mkdir(parents=True, exist_ok=True)


class ConfigManager:
    """Loads, validates, and manages configuration with hot reload."""

    def _find_config(self) -> Path:
        """Find the configuration file in expected locations."""
        # Check package-relative path first
        pkg_config = Path(__file__).resolve().parent.parent / "config" / "jarvis.yaml"
        if pkg_config.exists():
            return pkg_config
        # Check workspace-relative
        ws_config = Path.cwd() / "jarvis" / "config" / "jarvis.yaml"
        if ws_config.exists():
            return ws_config
        # Legacy: root config/
        legacy_config = Path.cwd() / "config" / "jarvis.yaml"
        if legacy_config.exists():
            return legacy_config
        return pkg_config

    def __init__(self):
        self.config: JarvisConfig = JarvisConfig()
        self._file_mtime: Optional[float] = None
        self._watcher_task: Optional[asyncio.Task] = None
        self._subscribers: List[Callable] = []
        # Determine config file location
        self.CONFIG_FILE = self._find_config()

    def load(self, path: Optional[Path] = None) -> JarvisConfig:
        """Load configuration from file."""
        config_path = path or self.CONFIG_FILE
        if config_path.exists():
            with open(config_path) as f:
                data = yaml.full_load(f) or {}
            # Override defaults with loaded values
            self._apply_overrides(data)
        else:
            # Create default config file
            self.save(self.config, config_path)
        # Convert path strings to Path objects before ensuring dirs
        from pathlib import Path
        for attr in ["workspace_root","data_dir","logs_dir","temp_dir","opencode_db_path","killswitch_path"]:
            val = getattr(self.config, attr)
            if isinstance(val, str):
                setattr(self.config, attr, Path(val))
        
        # Handle OpenCode AI integration: override LLM config if enabled
        if getattr(self.config, 'opencode_ai_enabled', False):
            oc_cfg_path = Path(self.config.opencode_ai_config_path).expanduser()
            if oc_cfg_path.exists():
                with open(oc_cfg_path) as f:
                    oc_data = yaml.safe_load(f) or {}
                if 'llm' in oc_data:
                    self.config.llm = oc_data['llm']
                    print(f"[Config] Using OpenCode AI config from {oc_cfg_path}")
                else:
                    print(f"[Config] OpenCode config has no 'llm' section, using default")
            else:
                print(f"[Config] opencode_ai enabled but config not found at {oc_cfg_path}, using default")

        # Log final LLM configuration
        llm_cfg = getattr(self.config, 'llm', {})
        provider = llm_cfg.get('provider', 'none')
        model = llm_cfg.get('model', 'unknown')
        print(f"[Config] Final LLM config: provider={provider}, model={model}")

        self.config.ensure_dirs()
        # Proxy computed path properties to ConfigManager for compatibility
        self.personas_dir = self.config.personas_dir
        self.patterns_dir = self.config.patterns_dir
        self.skills_dir = self.config.skills_dir
        self.archives_dir = self.config.archives_dir
        self.cache_dir = self.config.cache_dir
        self.history_db_path = self.config.history_db_path
        self.default_persona = self.config.default_persona
        self.auto_persona_switch = self.config.auto_persona_switch
        self.polling_interval_seconds = self.config.polling_interval_seconds
        # Proxy core path attributes for compatibility
        self.workspace_root = self.config.workspace_root
        self.data_dir = self.config.data_dir
        self.logs_dir = self.config.logs_dir
        self.temp_dir = self.config.temp_dir
        self.opencode_db_path = self.config.opencode_db_path
        self.killswitch_path = self.config.killswitch_path
        self._file_mtime = config_path.stat().st_mtime
        return self.config

    def _apply_overrides(self, data: Dict[str, Any]):
        """Apply loaded data to config, handling nested dicts."""
        for key, value in data.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            # Handle nested sections like 'safety', 'evolution', etc.
            elif isinstance(value, dict):
                for subkey, subval in value.items():
                    full_key = f"{key}_{subkey}"
                    if hasattr(self.config, full_key):
                        setattr(self.config, full_key, subval)

    def save(self, config: JarvisConfig, path: Optional[Path] = None) -> Path:
        """Save configuration to file."""
        config_path = path or self.CONFIG_FILE
        config_path.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(config)
        # Remove computed properties (they're @property, not fields)
        data.pop('personas_dir', None)
        data.pop('patterns_dir', None)
        data.pop('skills_dir', None)
        data.pop('archives_dir', None)
        data.pop('cache_dir', None)
        data.pop('history_db_path', None)
        with open(config_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        return config_path

    async def start_watcher(self, callback: Callable):
        """Watch config file for changes and reload automatically."""
        async def watch_loop():
            while True:
                await asyncio.sleep(5)
                if self.CONFIG_FILE.exists():
                    mtime = self.CONFIG_FILE.stat().st_mtime
                    if mtime != self._file_mtime:
                        self._file_mtime = mtime
                        try:
                            self.load()
                            callback()
                        except Exception as e:
                            print(f"[Config] Error reloading: {e}")

        self._watcher_task = asyncio.create_task(watch_loop())

    def stop_watcher(self):
        if self._watcher_task:
            self._watcher_task.cancel()