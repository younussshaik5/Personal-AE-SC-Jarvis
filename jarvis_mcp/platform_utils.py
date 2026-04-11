"""
Cross-platform compatibility utilities for JARVIS.
Handles Windows, Mac, and Linux differences in:
- Port checking and process management
- Signal handling
- Environment file parsing (.env)
- Path normalization
"""

import os
import sys
import signal
import socket
import subprocess
import atexit
from pathlib import Path
from typing import Optional, Dict, Callable

class PlatformUtils:
    """Platform-aware utilities for Windows, Mac, and Linux compatibility."""

    @staticmethod
    def is_windows() -> bool:
        """Check if running on Windows."""
        return sys.platform == "win32"

    @staticmethod
    def is_mac() -> bool:
        """Check if running on macOS."""
        return sys.platform == "darwin"

    @staticmethod
    def is_linux() -> bool:
        """Check if running on Linux."""
        return sys.platform == "linux"

    @staticmethod
    def check_port_available(port: int) -> bool:
        """
        Check if a port is available (cross-platform).

        Args:
            port: Port number to check

        Returns:
            True if port is available, False if in use
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                s.close()
            return True
        except (OSError, socket.error):
            return False

    @staticmethod
    def find_available_port(start_port: int = 8000, max_attempts: int = 100) -> Optional[int]:
        """
        Find an available port starting from start_port.

        Args:
            start_port: Initial port to try (default: 8000)
            max_attempts: Maximum number of ports to try (default: 100)

        Returns:
            Available port number, or None if no ports available
        """
        for offset in range(max_attempts):
            port = start_port + offset
            if PlatformUtils.check_port_available(port):
                return port
        return None

    @staticmethod
    def kill_process_on_port(port: int) -> bool:
        """
        Kill process listening on port (platform-aware).

        Args:
            port: Port number

        Returns:
            True if successful, False otherwise
        """
        try:
            if PlatformUtils.is_windows():
                # Windows: use taskkill with netstat output parsing
                result = subprocess.run(
                    ["netstat", "-ano"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                for line in result.stdout.splitlines():
                    if f":{port}" in line and "LISTENING" in line:
                        parts = line.split()
                        if parts:
                            pid = parts[-1]
                            subprocess.run(
                                ["taskkill", "/PID", pid, "/F"],
                                capture_output=True,
                                timeout=5,
                            )
                            return True
            else:
                # Mac/Linux: use lsof
                result = subprocess.run(
                    ["lsof", "-ti", f":{port}"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.stdout.strip():
                    pid = result.stdout.strip().split()[0]
                    subprocess.run(["kill", "-9", pid], timeout=5)
                    return True
        except Exception:
            pass
        return False

    @staticmethod
    def register_signal_handlers(handler: Callable) -> None:
        """
        Register graceful shutdown handlers (platform-aware).

        On Windows: uses atexit (signals not reliable)
        On Mac/Linux: uses SIGTERM and SIGINT

        Args:
            handler: Callable to invoke on shutdown
        """
        if PlatformUtils.is_windows():
            # Windows: signals are unreliable, use atexit
            atexit.register(handler)
        else:
            # Mac/Linux: use POSIX signals
            def signal_handler(signum, frame):
                handler()

            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)

    @staticmethod
    def load_env_file(env_path: Path) -> Dict[str, str]:
        """
        Load .env file with BOM and encoding handling.

        Handles:
        - UTF-8 BOM (common on Windows)
        - CRLF line endings (Windows)
        - Comments and empty lines

        Args:
            env_path: Path to .env file

        Returns:
            Dictionary of environment variables loaded
        """
        env_vars = {}

        # Try using python-dotenv first (preferred)
        try:
            from dotenv import load_dotenv

            load_dotenv(env_path, override=False)

            # Collect loaded vars
            for key in os.environ:
                if key.startswith(("NVIDIA_", "ANTHROPIC_", "JARVIS_", "CLAUDE_", "TELEGRAM_")):
                    env_vars[key] = os.environ[key]
            return env_vars
        except ImportError:
            pass

        # Fallback: manual parsing with BOM detection
        if not env_path.exists():
            return env_vars

        try:
            content = env_path.read_bytes()

            # Detect and skip UTF-8 BOM
            if content.startswith(b"\xef\xbb\xbf"):
                content = content[3:]

            text = content.decode("utf-8")

            # Parse lines
            for line in text.splitlines():
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                # Parse KEY=VALUE
                if "=" not in line:
                    continue

                k, _, v = line.partition("=")
                k = k.strip()
                v = v.strip().strip('"').strip("'")

                if k and k not in os.environ:
                    os.environ[k] = v
                    env_vars[k] = v

        except Exception as e:
            print(f"Warning: Failed to parse {env_path}: {e}")

        return env_vars

    @staticmethod
    def normalize_path(path: Path) -> str:
        """
        Normalize path for JSON serialization (use forward slashes).

        Args:
            path: Path object

        Returns:
            Path string with forward slashes
        """
        return str(path).replace("\\", "/")

    @staticmethod
    def get_python_executable() -> str:
        """
        Get the current Python executable path.

        Returns:
            Full path to Python executable
        """
        return str(Path(sys.executable).resolve())

    @staticmethod
    def get_venv_path() -> Optional[Path]:
        """
        Get virtual environment path if activated.

        Returns:
            Path to venv, or None if not activated
        """
        venv_path = os.getenv("VIRTUAL_ENV")
        if venv_path:
            return Path(venv_path)
        return None

    @staticmethod
    def ensure_venv_activated() -> Path:
        """
        Ensure virtual environment is activated.

        Returns:
            Path to venv

        Raises:
            RuntimeError if venv is not activated
        """
        venv_path = PlatformUtils.get_venv_path()
        if not venv_path:
            if PlatformUtils.is_windows():
                raise RuntimeError(
                    "Virtual environment not activated.\n"
                    "Run: venv\\Scripts\\activate.bat"
                )
            else:
                raise RuntimeError(
                    "Virtual environment not activated.\n"
                    "Run: source venv/bin/activate"
                )
        return venv_path

    @staticmethod
    def get_os_name() -> str:
        """Get OS name for logging/display."""
        if PlatformUtils.is_windows():
            return "Windows"
        elif PlatformUtils.is_mac():
            return "macOS"
        elif PlatformUtils.is_linux():
            return "Linux"
        else:
            return "Unknown"
