"""Configuration management for JARVIS."""

import os
from pathlib import Path
from typing import Optional, Dict, Any


class ConfigManager:
    """Manages JARVIS configuration from environment and config files."""

    def __init__(self):
        """Initialize config manager from environment variables."""
        # Account paths
        self.accounts_root = Path(
            os.getenv(
                "ACCOUNTS_ROOT",
                Path.home() / "Documents" / "claude space" / "ACCOUNTS"
            )
        ).expanduser()
        
        # Memory paths
        self.memory_root = Path(
            os.getenv(
                "MEMORY_ROOT",
                Path.home() / "Documents" / "claude space" / "MEMORY"
            )
        ).expanduser()

        # Create directories if they don't exist
        self.accounts_root.mkdir(parents=True, exist_ok=True)
        self.memory_root.mkdir(parents=True, exist_ok=True)

        # API Keys from environment
        self.nvidia_api_key = os.getenv("NVIDIA_API_KEY", "")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")

    def get_accounts_root(self) -> Path:
        """Get the accounts root directory."""
        return self.accounts_root

    def get_account_path(self, account_name: str) -> Path:
        """Get the path to an account directory."""
        # Remove spaces and special characters for folder names
        safe_name = account_name.replace(" ", "_").replace("/", "_")
        return self.accounts_root / safe_name

    def get_memory_root(self) -> Path:
        """Get the memory root directory."""
        return self.memory_root

    def get_api_key(self, provider: str = "nvidia") -> str:
        """Get API key for a provider."""
        if provider == "nvidia":
            return self.nvidia_api_key
        elif provider == "anthropic":
            return self.anthropic_api_key
        return ""

    def validate(self) -> Dict[str, Any]:
        """Validate configuration."""
        errors = []
        warnings = []

        # Check accounts root exists
        if not self.accounts_root.exists():
            warnings.append(f"Accounts root does not exist: {self.accounts_root}")

        # Check API keys
        if not self.nvidia_api_key:
            warnings.append("NVIDIA_API_KEY not set")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
