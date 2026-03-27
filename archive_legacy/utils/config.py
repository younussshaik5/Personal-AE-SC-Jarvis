"""
Configuration management for JARVIS.
Loads from environment variables, config files, and defaults.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class DatabaseConfig:
    """Database configuration"""
    type: str = "sqlite"
    path: str = "data/history/jarvis.db"
    pool_size: int = 5
    timeout: int = 30


@dataclass
class ObserverConfig:
    """Observer configuration"""
    file_system_enabled: bool = True
    git_enabled: bool = True
    database_enabled: bool = False
    conversations_enabled: bool = True
    scan_interval_seconds: int = 300  # 5 minutes
    watch_paths: list = field(default_factory=list)
    ignore_patterns: list = field(default_factory=lambda: [
        ".git", "__pycache__", "node_modules", ".venv", "venv",
        ".jarvisignore", "logs", "tmp", "temp"
    ])


@dataclass
class LearnerConfig:
    """Learner configuration"""
    pattern_min_frequency: int = 3
    confidence_threshold: float = 0.7
    learning_rate: float = 0.1
    max_patterns_per_category: int = 1000
    trend_detection_window_days: int = 7
    auto_evolution_enabled: bool = True
    evolution_check_interval_hours: int = 6


@dataclass
class UpdaterConfig:
    """Updater configuration"""
    max_file_size_mb: int = 10
    backup_before_modification: bool = True
    preserve_comments: bool = True
    auto_test_after_modification: bool = True
    max_concurrent_modifications: int = 3
    dry_run_mode: bool = False
    approval_required_risk_level: str = "high"  # low, medium, high


@dataclass
class PersonaConfig:
    """Persona configuration"""
    default_persona: str = "default"
    auto_switch_enabled: bool = True
    switch_threshold_score: float = 0.8
    history_retention_days: int = 365
    performance_tracking_enabled: bool = True


@dataclass
class MCPConfig:
    """MCP configuration"""
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    context_window_size: int = 4000
    max_skills_per_context: int = 10
    skill_selection_timeout_seconds: int = 5
    enable_semantic_search: bool = True
    cache_embeddings: bool = True
    cache_dir: str = "data/cache/mcp"


@dataclass
class ArchiveConfig:
    """Archive configuration"""
    archive_enabled: bool = True
    retention_policy_days: Dict[str, int] = field(default_factory=lambda: {
        "daily": 30,
        "weekly": 12,
        "monthly": 24,
        "yearly": 10
    })
    compression_level: int = 6
    encryption_enabled: bool = False
    encryption_key: Optional[str] = None
    archive_dir: str = "data/archives"
    max_concurrent_archives: int = 2


@dataclass
class SafetyConfig:
    """Safety and approval configuration"""
    auto_approve_low_risk: bool = True
    require_approval_medium_risk: bool = True
    require_approval_high_risk: bool = True
    risk_assessment_enabled: bool = True
    impact_analysis_enabled: bool = True
    rollback_enabled: bool = True
    backup_retention_count: int = 10
    kill_switch_enabled: bool = True
    kill_switch_file: str = ".jarvis.killswitch"


@dataclass
class APIConfig:
    """API server configuration"""
    enabled: bool = False
    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = 4
    cors_enabled: bool = True
    auth_required: bool = False
    jwt_secret: Optional[str] = None
    rate_limit_requests_per_minute: int = 100


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    log_to_file: bool = True
    log_to_console: bool = True
    log_dir: str = "logs"
    json_format: bool = True
    max_bytes: int = 10_485_760  # 10 MB
    backup_count: int = 10


@dataclass
class Config:
    """Main configuration container"""

    # Version
    version: str = "0.1.0"

    # Core settings
    name: str = "JARVIS"
    environment: str = "development"  # development, staging, production
    debug: bool = False

    # Paths
    root_dir: str = "."
    data_dir: str = "data"
    workspace_paths: list = field(default_factory=list)

    # Component configs
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    observer: ObserverConfig = field(default_factory=ObserverConfig)
    learner: LearnerConfig = field(default_factory=LearnerConfig)
    updater: UpdaterConfig = field(default_factory=UpdaterConfig)
    persona: PersonaConfig = field(default_factory=PersonaConfig)
    mcp: MCPConfig = field(default_factory=MCPConfig)
    archive: ArchiveConfig = field(default_factory=ArchiveConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    api: APIConfig = field(default_factory=APIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    # Performance
    max_concurrent_tasks: int = 10
    event_queue_size: int = 10000
    metrics_retention_days: int = 30

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        """
        Load configuration from file and environment.

        Args:
            config_path: Path to config file (JSON). If None, uses default locations.

        Returns:
            Loaded Config instance
        """
        config = cls()

        # Try to load from file
        if config_path:
            config_file = Path(config_path)
        else:
            # Check multiple locations
            possible_paths = [
                "jarvis_config.json",
                "config/jarvis.json",
                ".jarvis/config.json",
                Path.home() / ".jarvis" / "config.json"
            ]
            config_file = None
            for path in possible_paths:
                if Path(path).exists():
                    config_file = Path(path)
                    break

        if config_file and config_file.exists():
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                config = cls._update_from_dict(config, file_config)

        # Override with environment variables
        config = cls._update_from_env(config)

        # Resolve paths
        root_path = Path(config.root_dir).expanduser().resolve()
        config.root_dir = str(root_path)
        config.data_dir = str((root_path / config.data_dir).resolve())
        config.database.path = str((Path(config.data_dir) / "history" / "jarvis.db").resolve())
        config.archive.archive_dir = str((Path(config.data_dir) / "archives").resolve())
        config.mcp.cache_dir = str((Path(config.data_dir) / "cache" / "mcp").resolve())
        config.logging.log_dir = str(root_path / config.logging.log_dir)

        return config

    @classmethod
    def _update_from_dict(cls, config: "Config", data: Dict[str, Any]) -> "Config":
        """Recursively update config from dictionary"""
        for key, value in data.items():
            if hasattr(config, key):
                attr = getattr(config, key)
                if isinstance(attr, (list, dict)) and not isinstance(attr, (str, bytes)):
                    # Merge dicts/lists
                    if isinstance(attr, dict):
                        attr.update(value)
                    elif isinstance(attr, list):
                        attr.extend(value)
                elif hasattr(attr, '__dict__'):
                    # It's a dataclass, update its fields
                    for subkey, subvalue in value.items():
                        if hasattr(attr, subkey):
                            setattr(attr, subkey, subvalue)
                else:
                    setattr(config, key, value)
        return config

    @classmethod
    def _update_from_env(cls, config: "Config") -> "Config":
        """Update config from environment variables"""
        env_map = {
            "JARVIS_ENVIRONMENT": ("environment", str),
            "JARVIS_DEBUG": ("debug", bool),
            "JARVIS_ROOT_DIR": ("root_dir", str),
            "JARVIS_LOG_LEVEL": ("logging.level", str),
            "JARVIS_DB_PATH": ("database.path", str),
            "JARVIS_API_ENABLED": ("api.enabled", bool),
            "JARVIS_API_PORT": ("api.port", int),
            "JARVIS_WORKSPACE_PATHS": ("workspace_paths", lambda x: x.split(':')),
        }

        for env_var, (attr_path, cast_func) in env_map.items():
            if env_var in os.environ:
                value = os.environ[env_var]
                try:
                    cast_value = cast_func(value)
                    # Navigate to nested attribute
                    parts = attr_path.split('.')
                    obj = config
                    for part in parts[:-1]:
                        obj = getattr(obj, part)
                    setattr(obj, parts[-1], cast_value)
                except (ValueError, AttributeError) as e:
                    print(f"Warning: Could not parse {env_var}={value}: {e}")

        return config

    def save(self, path: Optional[str] = None) -> str:
        """Save configuration to file"""
        if path is None:
            path = "config/jarvis.json"

        config_path = Path(path)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict
        config_dict = {
            "version": self.version,
            "name": self.name,
            "environment": self.environment,
            "debug": self.debug,
            "root_dir": str(self.root_dir),
            "data_dir": str(self.data_dir),
            "workspace_paths": self.workspace_paths,
            "database": {
                "type": self.database.type,
                "path": str(self.database.path),
                "pool_size": self.database.pool_size,
                "timeout": self.database.timeout,
            },
            "observer": {
                "file_system_enabled": self.observer.file_system_enabled,
                "git_enabled": self.observer.git_enabled,
                "database_enabled": self.observer.database_enabled,
                "conversations_enabled": self.observer.conversations_enabled,
                "scan_interval_seconds": self.observer.scan_interval_seconds,
                "watch_paths": self.observer.watch_paths,
                "ignore_patterns": self.observer.ignore_patterns,
            },
            "learner": {
                "pattern_min_frequency": self.learner.pattern_min_frequency,
                "confidence_threshold": self.learner.confidence_threshold,
                "learning_rate": self.learner.learning_rate,
                "max_patterns_per_category": self.learner.max_patterns_per_category,
            },
            "updater": {
                "max_file_size_mb": self.updater.max_file_size_mb,
                "backup_before_modification": self.updater.backup_before_modification,
                "preserve_comments": self.updater.preserve_comments,
            },
            "persona": {
                "default_persona": self.persona.default_persona,
                "auto_switch_enabled": self.persona.auto_switch_enabled,
            },
            "mcp": {
                "embedding_model": self.mcp.embedding_model,
                "context_window_size": self.mcp.context_window_size,
                "max_skills_per_context": self.mcp.max_skills_per_context,
                "enable_semantic_search": self.mcp.enable_semantic_search,
            },
            "archive": {
                "archive_enabled": self.archive.archive_enabled,
                "retention_policy_days": self.archive.retention_policy_days,
                "compression_level": self.archive.compression_level,
            },
            "safety": {
                "auto_approve_low_risk": self.safety.auto_approve_low_risk,
                "require_approval_medium_risk": self.safety.require_approval_medium_risk,
                "require_approval_high_risk": self.safety.require_approval_high_risk,
                "rollback_enabled": self.safety.rollback_enabled,
            },
            "api": {
                "enabled": self.api.enabled,
                "host": self.api.host,
                "port": self.api.port,
                "workers": self.api.workers,
            },
            "logging": {
                "level": self.logging.level,
                "log_to_file": self.logging.log_to_file,
                "log_to_console": self.logging.log_to_console,
                "log_dir": str(self.logging.log_dir),
                "json_format": self.logging.json_format,
            },
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "event_queue_size": self.event_queue_size,
        }

        with open(config_path, 'w') as f:
            json.dump(config_dict, f, indent=2)

        return str(config_path)

    def get_workspace_paths(self) -> list:
        """Get list of workspace paths as Path objects"""
        return [Path(p).resolve() for p in self.workspace_paths]
