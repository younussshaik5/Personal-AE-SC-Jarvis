"""Configuration management for JARVIS."""

import os
import re
import logging
from pathlib import Path
from typing import Optional, Dict, Any

log = logging.getLogger(__name__)


class ConfigManager:
    """Manages JARVIS configuration from environment and config files."""

    def __init__(self):
        """Initialize config manager from environment variables."""
        # Get JARVIS_HOME - fail if not set
        jarvis_home = os.getenv("JARVIS_HOME")
        if not jarvis_home:
            raise RuntimeError(
                "JARVIS_HOME environment variable not set. "
                "Run setup.bat (Windows) or setup.sh (Mac/Linux) to initialize."
            )

        jarvis_home_path = Path(jarvis_home).expanduser()

        # Verify JARVIS_HOME is accessible
        if not jarvis_home_path.exists():
            raise RuntimeError(
                f"JARVIS_HOME does not exist: {jarvis_home_path}. "
                "Run setup.bat or setup.sh to initialize."
            )

        # Account paths
        self.accounts_root = jarvis_home_path / "ACCOUNTS"

        # Memory paths
        self.memory_root = jarvis_home_path / "MEMORY"

        # Create directories if they don't exist — fail fast with clear error if impossible
        try:
            self.accounts_root.mkdir(parents=True, exist_ok=True)
            self.memory_root.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise RuntimeError(
                f"JARVIS cannot create required directories: {e}. "
                f"Check permissions on {self.accounts_root.parent}"
            ) from e

        # API Keys from environment
        self.nvidia_api_key = os.getenv("NVIDIA_API_KEY", "")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")

    def get_accounts_root(self) -> Path:
        """Get the accounts root directory."""
        return self.accounts_root

    def get_account_path(self, account_name: str) -> Path:
        """
        Get the path to an account directory with security validation.

        Prevents path traversal attacks by:
        1. Validating account_name contains only safe characters
        2. Resolving the final path and verifying it's within accounts_root
        3. Rejecting any path components that escape the accounts directory

        Args:
            account_name: The account name (e.g., "AcmeCorp")

        Returns:
            Path object to the account directory

        Raises:
            ValueError: If account_name is invalid or attempts path traversal
        """
        # Validate: only alphanumeric, underscores, hyphens, and spaces
        if not account_name or not isinstance(account_name, str):
            raise ValueError("account_name must be a non-empty string")

        # Normalize spaces to underscores, validate safe characters
        safe_name = account_name.strip().replace(" ", "_")

        # Whitelist: only allow [a-zA-Z0-9_-]
        if not re.match(r"^[a-zA-Z0-9_\-]+$", safe_name):
            raise ValueError(
                f"Invalid account name '{account_name}'. "
                "Only alphanumeric characters, underscores, and hyphens allowed."
            )

        # Build path
        account_path = self.accounts_root / safe_name

        # Security check: verify resolved path is within accounts_root
        try:
            account_path.resolve().relative_to(self.accounts_root.resolve())
        except ValueError as e:
            # Path is outside accounts_root
            log.error(f"Path traversal attempt detected: {account_name}")
            raise ValueError(f"Path traversal not allowed: {account_name}") from e

        return account_path

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
