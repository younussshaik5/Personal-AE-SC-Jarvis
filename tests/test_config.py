"""
Unit tests for ConfigManager — validates environment setup, path safety, and configuration.

Tests:
  - JARVIS_HOME required and validated
  - Account path whitelist (alphanumeric + underscore + hyphen only)
  - Path traversal prevention (relative_to check)
  - Configuration values validated on startup (timeout, port, log limits)
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add jarvis_mcp to path for test imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from jarvis_mcp.config.config_manager import ConfigManager


class TestConfigManagerEnvironment:
    """Test JARVIS_HOME environment variable handling."""

    def test_jarvis_home_required(self, tmp_path):
        """JARVIS_HOME must be set on startup."""
        with patch.dict(os.environ, {}, clear=False):
            if "JARVIS_HOME" in os.environ:
                del os.environ["JARVIS_HOME"]
            with pytest.raises(RuntimeError, match="JARVIS_HOME.*not set"):
                ConfigManager()

    def test_jarvis_home_with_valid_path(self, tmp_path):
        """ConfigManager initializes if JARVIS_HOME is valid."""
        accounts_dir = tmp_path / "ACCOUNTS"
        accounts_dir.mkdir(parents=True)

        with patch.dict(os.environ, {"JARVIS_HOME": str(tmp_path)}):
            config = ConfigManager()
            assert config.accounts_root == accounts_dir
            assert config.accounts_root.exists()

    def test_jarvis_home_path_not_exist(self, tmp_path):
        """ConfigManager fails if ACCOUNTS directory doesn't exist."""
        jarvis_home = tmp_path / "nonexistent"
        with patch.dict(os.environ, {"JARVIS_HOME": str(jarvis_home)}):
            with pytest.raises(RuntimeError, match="ACCOUNTS directory not found"):
                ConfigManager()


class TestAccountPathWhitelist:
    """Test account name validation (path traversal prevention)."""

    @pytest.fixture
    def config(self, tmp_path):
        """Fixture: valid ConfigManager with temp ACCOUNTS directory."""
        accounts_dir = tmp_path / "ACCOUNTS"
        accounts_dir.mkdir(parents=True)
        with patch.dict(os.environ, {"JARVIS_HOME": str(tmp_path)}):
            return ConfigManager()

    def test_valid_account_names(self, config):
        """Valid account names pass validation."""
        valid_names = [
            "AcmeCorp",
            "acme-corp",
            "acme_corp",
            "ACME_CORP_123",
            "client-1",
        ]
        for name in valid_names:
            # Create the directory so path exists
            (config.accounts_root / name).mkdir(exist_ok=True)
            path = config.get_account_path(name)
            assert path == config.accounts_root / name

    def test_path_traversal_attempts_blocked(self, config):
        """Path traversal attempts (../) are rejected."""
        traversal_names = [
            "../../../etc/passwd",
            "acme/../../../etc",
            "acme/..",
            "acme/../../secret",
            "..",
            ".",
        ]
        for name in traversal_names:
            with pytest.raises(ValueError, match="Invalid account name"):
                config.get_account_path(name)

    def test_special_characters_blocked(self, config):
        """Special characters are rejected in account names."""
        invalid_names = [
            "acme;rm -rf",
            "acme`whoami`",
            "acme$(whoami)",
            "acme|cat",
            "acme&ls",
            "acme|whoami",
            "acme\necho",
            "acme\\etc",
        ]
        for name in invalid_names:
            with pytest.raises(ValueError, match="Invalid account name"):
                config.get_account_path(name)

    def test_account_not_found(self, config):
        """Accessing non-existent account returns None."""
        path = config.get_account_path("NonexistentAccount")
        assert path is None

    def test_nested_account_found(self, config):
        """Nested accounts (parent/child) are found."""
        parent = config.accounts_root / "parent"
        parent.mkdir(exist_ok=True)
        child = parent / "child"
        child.mkdir(exist_ok=True)

        path = config.get_account_path("child")
        assert path == child


class TestConfigurationValidation:
    """Test configuration value validation."""

    @pytest.fixture
    def config(self, tmp_path):
        """Fixture: valid ConfigManager."""
        accounts_dir = tmp_path / "ACCOUNTS"
        accounts_dir.mkdir(parents=True)
        with patch.dict(os.environ, {"JARVIS_HOME": str(tmp_path)}):
            return ConfigManager()

    def test_skill_timeout_positive(self, config):
        """Skill timeout must be positive."""
        assert config.skill_timeout > 0
        assert config.skill_timeout == 600  # Default

    def test_skill_timeout_from_env(self, tmp_path):
        """Skill timeout reads from JARVIS_SKILL_TIMEOUT env var."""
        accounts_dir = tmp_path / "ACCOUNTS"
        accounts_dir.mkdir(parents=True)
        with patch.dict(os.environ, {
            "JARVIS_HOME": str(tmp_path),
            "JARVIS_SKILL_TIMEOUT": "300"
        }):
            config = ConfigManager()
            assert config.skill_timeout == 300

    def test_skill_timeout_invalid_reverts_to_default(self, tmp_path):
        """Invalid timeout reverts to default (600)."""
        accounts_dir = tmp_path / "ACCOUNTS"
        accounts_dir.mkdir(parents=True)
        with patch.dict(os.environ, {
            "JARVIS_HOME": str(tmp_path),
            "JARVIS_SKILL_TIMEOUT": "invalid"
        }):
            config = ConfigManager()
            assert config.skill_timeout == 600  # Default

    def test_crm_port_valid_range(self, config):
        """CRM port is between 1 and 65535."""
        assert 1 <= config.crm_port <= 65535
        assert config.crm_port == 8000  # Default

    def test_crm_port_from_env(self, tmp_path):
        """CRM port reads from CRM_PORT env var."""
        accounts_dir = tmp_path / "ACCOUNTS"
        accounts_dir.mkdir(parents=True)
        with patch.dict(os.environ, {
            "JARVIS_HOME": str(tmp_path),
            "CRM_PORT": "9000"
        }):
            config = ConfigManager()
            assert config.crm_port == 9000

    def test_crm_port_invalid_reverts_to_default(self, tmp_path):
        """Invalid port reverts to default (8000)."""
        accounts_dir = tmp_path / "ACCOUNTS"
        accounts_dir.mkdir(parents=True)
        with patch.dict(os.environ, {
            "JARVIS_HOME": str(tmp_path),
            "CRM_PORT": "99999"
        }):
            config = ConfigManager()
            assert config.crm_port == 8000  # Default

    def test_max_log_lines_positive(self, config):
        """Max log lines must be positive."""
        assert config.max_log_lines > 0
        assert config.max_log_lines == 200  # Default

    def test_max_log_lines_from_env(self, tmp_path):
        """Max log lines reads from JARVIS_MAX_LOG_LINES env var."""
        accounts_dir = tmp_path / "ACCOUNTS"
        accounts_dir.mkdir(parents=True)
        with patch.dict(os.environ, {
            "JARVIS_HOME": str(tmp_path),
            "JARVIS_MAX_LOG_LINES": "500"
        }):
            config = ConfigManager()
            assert config.max_log_lines == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
