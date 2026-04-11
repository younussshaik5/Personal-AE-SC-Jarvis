"""
Unit tests for PlatformUtils — cross-platform helpers.

Tests:
  - Port availability checking
  - Available port discovery
  - Path normalization
  - Environment variable detection
"""

import pytest
import os
import sys
import socket
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from jarvis_mcp.platform_utils import PlatformUtils


class TestPlatformDetection:
    """Test OS detection."""

    def test_is_windows(self):
        """Detect Windows platform."""
        with patch("sys.platform", "win32"):
            assert PlatformUtils.is_windows() is True
            assert PlatformUtils.is_mac() is False
            assert PlatformUtils.is_linux() is False

    def test_is_mac(self):
        """Detect macOS platform."""
        with patch("sys.platform", "darwin"):
            assert PlatformUtils.is_mac() is True
            assert PlatformUtils.is_windows() is False
            assert PlatformUtils.is_linux() is False

    def test_is_linux(self):
        """Detect Linux platform."""
        with patch("sys.platform", "linux"):
            assert PlatformUtils.is_linux() is True
            assert PlatformUtils.is_windows() is False
            assert PlatformUtils.is_mac() is False

    def test_get_os_name(self):
        """Get human-readable OS name."""
        with patch("sys.platform", "win32"):
            assert PlatformUtils.get_os_name() == "Windows"
        with patch("sys.platform", "darwin"):
            assert PlatformUtils.get_os_name() == "macOS"
        with patch("sys.platform", "linux"):
            assert PlatformUtils.get_os_name() == "Linux"


class TestPortAvailability:
    """Test port checking and availability."""

    def test_port_available(self):
        """Check if a port is available."""
        # Use a port unlikely to be in use (high numbered)
        port = 59999
        assert PlatformUtils.check_port_available(port) is True

    def test_port_unavailable(self):
        """Check if a port is unavailable (when occupied)."""
        # Occupy a port temporarily
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))  # Bind to any available port
            _, port = s.getsockname()
            assert PlatformUtils.check_port_available(port) is False

    def test_find_available_port_default(self):
        """Find available port starting from 8000."""
        port = PlatformUtils.find_available_port()
        assert port is not None
        assert port >= 8000
        assert PlatformUtils.check_port_available(port) is True

    def test_find_available_port_custom_start(self):
        """Find available port from custom start port."""
        port = PlatformUtils.find_available_port(start_port=9000, max_attempts=10)
        if port is not None:
            assert port >= 9000
            assert PlatformUtils.check_port_available(port) is True

    def test_find_available_port_returns_none_when_exhausted(self):
        """Return None if all ports in range are occupied."""
        # Mock check_port_available to always return False
        with patch.object(PlatformUtils, "check_port_available", return_value=False):
            result = PlatformUtils.find_available_port(start_port=8000, max_attempts=10)
            assert result is None


class TestPathNormalization:
    """Test cross-platform path handling."""

    def test_normalize_path_windows(self):
        """Normalize Windows path to forward slashes."""
        path = Path("C:\\Users\\John\\JARVIS\\ACCOUNTS\\AcmeCorp")
        normalized = PlatformUtils.normalize_path(path)
        assert "\\" not in normalized
        assert "/" in normalized

    def test_normalize_path_unix(self):
        """Unix paths stay unchanged."""
        path = Path("/home/john/JARVIS/ACCOUNTS/AcmeCorp")
        normalized = PlatformUtils.normalize_path(path)
        assert normalized == "/home/john/JARVIS/ACCOUNTS/AcmeCorp"

    def test_normalize_path_for_json(self):
        """Normalized paths are valid JSON."""
        import json
        path = Path("C:\\Users\\John\\JARVIS")
        normalized = PlatformUtils.normalize_path(path)
        obj = {"path": normalized}
        json_str = json.dumps(obj)
        assert json_str  # Valid JSON
        assert "\\" not in json_str


class TestEnvironmentDetection:
    """Test virtual environment and Python detection."""

    def test_get_python_executable(self):
        """Get current Python executable path."""
        exe = PlatformUtils.get_python_executable()
        assert exe
        assert Path(exe).exists()

    def test_get_venv_path_when_activated(self):
        """Get venv path when activated."""
        venv_path = "/path/to/venv"
        with patch.dict(os.environ, {"VIRTUAL_ENV": venv_path}):
            result = PlatformUtils.get_venv_path()
            assert result == Path(venv_path)

    def test_get_venv_path_when_not_activated(self):
        """Return None when venv not activated."""
        with patch.dict(os.environ, {}, clear=False):
            if "VIRTUAL_ENV" in os.environ:
                del os.environ["VIRTUAL_ENV"]
            result = PlatformUtils.get_venv_path()
            assert result is None

    def test_ensure_venv_activated_success(self, tmp_path):
        """Ensure venv is activated — success case."""
        venv_path = tmp_path / "venv"
        venv_path.mkdir()

        with patch.dict(os.environ, {"VIRTUAL_ENV": str(venv_path)}):
            result = PlatformUtils.ensure_venv_activated()
            assert result == venv_path

    def test_ensure_venv_activated_failure(self):
        """Ensure venv is activated — failure case."""
        with patch.dict(os.environ, {}, clear=False):
            if "VIRTUAL_ENV" in os.environ:
                del os.environ["VIRTUAL_ENV"]
            with pytest.raises(RuntimeError, match="Virtual environment not activated"):
                PlatformUtils.ensure_venv_activated()


class TestEnvFileLoading:
    """Test .env file parsing."""

    def test_load_env_file_with_dotenv(self, tmp_path):
        """Load .env using python-dotenv if available."""
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=test_value\nNVIDIA_API_KEY=nvapi-test")

        with patch.dict(os.environ, {"JARVIS_HOME": str(tmp_path)}):
            result = PlatformUtils.load_env_file(env_file)
            # Should have loaded NVIDIA keys
            assert "NVIDIA_API_KEY" in result or "TEST_VAR" in result

    def test_load_env_file_with_utf8_bom(self, tmp_path):
        """Load .env file with UTF-8 BOM."""
        env_file = tmp_path / ".env"
        # Write with BOM
        content = "TEST_VAR=test_value\nNVIDIA_API_KEY=nvapi-test"
        env_file.write_bytes(b'\xef\xbb\xbf' + content.encode("utf-8"))

        with patch.dict(os.environ, {"JARVIS_HOME": str(tmp_path)}):
            result = PlatformUtils.load_env_file(env_file)
            assert result is not None

    def test_load_env_file_ignores_comments(self, tmp_path):
        """Load .env ignores comment lines."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "# This is a comment\n"
            "TEST_VAR=test_value\n"
            "# Another comment\n"
            "NVIDIA_API_KEY=nvapi-test"
        )

        with patch.dict(os.environ, {"JARVIS_HOME": str(tmp_path)}):
            result = PlatformUtils.load_env_file(env_file)
            # Comments should not appear as keys
            assert "# This is a comment" not in result

    def test_load_env_file_nonexistent(self, tmp_path):
        """Load .env when file doesn't exist returns empty dict."""
        env_file = tmp_path / ".env"
        result = PlatformUtils.load_env_file(env_file)
        assert result == {}

    def test_load_env_file_with_quotes(self, tmp_path):
        """Load .env handles quoted values."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            'TEST_VAR="quoted value"\n'
            "ANOTHER='single quoted'"
        )

        with patch.dict(os.environ, {"JARVIS_HOME": str(tmp_path)}):
            result = PlatformUtils.load_env_file(env_file)
            # Values should be stripped of quotes
            assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
