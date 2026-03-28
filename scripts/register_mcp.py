#!/usr/bin/env python3
"""
Register JARVIS MCP server with Claude Desktop configuration.
Detects OS, finds config file, adds/updates JARVIS entry.
"""

import json
import os
import sys
from pathlib import Path


def get_claude_config_path() -> Path:
    """Get Claude Desktop config path based on OS."""
    system = sys.platform
    if system == "darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif system == "linux":
        return Path.home() / ".config" / "claude" / "claude_desktop_config.json"
    elif system == "win32":
        appdata = os.environ.get("APPDATA", "")
        return Path(appdata) / "Claude" / "claude_desktop_config.json"
    else:
        print(f"  WARNING: Unknown platform '{system}', skipping MCP registration")
        return None


def register_jarvis_mcp():
    """Register JARVIS MCP server in Claude Desktop config."""
    config_path = get_claude_config_path()
    if config_path is None:
        return

    # Get repo root (parent of scripts/)
    repo_root = Path(__file__).resolve().parent.parent
    mcp_server_path = repo_root / "mcp-jarvis-server" / "dist" / "index.js"

    # JARVIS data directory
    jarvis_home = os.environ.get("JARVIS_HOME", str(Path.home() / "Documents" / "claude space" / "JARVIS"))

    # Build MCP server entry
    jarvis_entry = {
        "command": "node",
        "args": [str(mcp_server_path)],
        "env": {
            "JARVIS_DATA_DIR": jarvis_home
        }
    }

    # Load or create config
    config = {}
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
        except (json.JSONDecodeError, IOError):
            print(f"  WARNING: Could not parse {config_path}, creating fresh config")
            config = {}

    # Ensure mcpServers section exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}

    # Add/update JARVIS entry
    config["mcpServers"]["jarvis"] = jarvis_entry

    # Write config
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2) + "\n")

    print(f"  Registered JARVIS MCP server in: {config_path}")
    print(f"  MCP server path: {mcp_server_path}")
    print(f"  JARVIS data dir: {jarvis_home}")

    # Also register with OpenCode if installed
    register_opencode_mcp(repo_root, jarvis_home)


def register_opencode_mcp(repo_root: Path, jarvis_home: str):
    """Register with OpenCode if its config exists."""
    opencode_config = Path.home() / ".config" / "opencode" / "config.json"
    if not opencode_config.exists():
        return

    try:
        config = json.loads(opencode_config.read_text())
    except (json.JSONDecodeError, IOError):
        return

    if "mcpServers" not in config:
        config["mcpServers"] = {}

    mcp_server_path = repo_root / "mcp-jarvis-server" / "dist" / "index.js"
    config["mcpServers"]["jarvis"] = {
        "command": "node",
        "args": [str(mcp_server_path)],
        "env": {
            "JARVIS_DATA_DIR": jarvis_home
        }
    }

    opencode_config.write_text(json.dumps(config, indent=2) + "\n")
    print(f"  Also registered with OpenCode: {opencode_config}")


if __name__ == "__main__":
    register_jarvis_mcp()
