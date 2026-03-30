#!/usr/bin/env python3
"""
Register JARVIS MCP servers with Claude Code (CLI) and Claude Desktop.
Runs on every `start_jarvis.sh` call — fully idempotent.

Writes to:
  1. ~/.claude/settings.json          — Claude Code global (all directories)
  2. <repo>/.claude/settings.json     — Claude Code project-level (this repo)
  3. Claude Desktop claude_desktop_config.json  — Claude Desktop app (macOS/Linux/Win)
"""

import json
import os
import shutil
import sys
from pathlib import Path


# ── Helpers ──────────────────────────────────────────────────────────────────

def find_node() -> str:
    """Return the full path to a node binary ≥18, or 'node' as fallback."""
    # 1. NODE_BIN env var set by start_jarvis.sh
    env_node = os.environ.get("NODE_BIN", "")
    if env_node and Path(env_node).exists():
        return env_node

    # 2. node in PATH
    found = shutil.which("node")
    if found:
        return found

    # 3. Common fixed locations
    candidates = [
        "/opt/homebrew/bin/node",
        "/usr/local/bin/node",
        "/usr/bin/node",
    ]
    for c in candidates:
        if Path(c).exists():
            return c

    # 4. nvm — highest version
    nvm_root = Path.home() / ".nvm" / "versions" / "node"
    if nvm_root.is_dir():
        versions = sorted(nvm_root.iterdir(), key=lambda p: p.name)
        for v in reversed(versions):
            node = v / "bin" / "node"
            if node.exists():
                return str(node)

    return "node"  # last-resort bare name


def read_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def merge_mcp_servers(config: dict, servers: dict) -> bool:
    """Merge servers into config['mcpServers']. Returns True if config changed."""
    existing = config.get("mcpServers", {})
    changed = False
    for name, entry in servers.items():
        if existing.get(name) != entry:
            existing[name] = entry
            changed = True
    if changed:
        config["mcpServers"] = existing
    return changed


# ── Build server entries ──────────────────────────────────────────────────────

def build_server_entries(repo_root: Path, jarvis_home: str, node_bin: str) -> dict:
    mcp_server = repo_root / "mcp-jarvis-server" / "dist" / "index.js"
    observer   = repo_root / "mcp-opencode-observer" / "dist" / "index.js"

    servers = {
        "jarvis": {
            "command": node_bin,
            "args": [str(mcp_server)],
            "env": {"JARVIS_DATA_DIR": jarvis_home},
        }
    }
    if observer.exists():
        servers["jarvis-opencode-observer"] = {
            "command": node_bin,
            "args": [str(observer)],
            "env": {
                "JARVIS_DATA_DIR": jarvis_home,
                "OPENCODE_OBSERVER_PORT": "3000",
                "OPENCODE_OBSERVER_WS_PORT": "3001",
            },
        }
    return servers


# ── Registration targets ──────────────────────────────────────────────────────

def register_claude_code_global(servers: dict) -> bool:
    """Register in ~/.claude/settings.json (Claude Code global)."""
    path = Path.home() / ".claude" / "settings.json"
    config = read_json(path)
    changed = merge_mcp_servers(config, servers)
    if changed:
        write_json(path, config)
    return changed


def register_claude_code_project(repo_root: Path, servers: dict) -> bool:
    """Register in <repo>/.claude/settings.json (project-level)."""
    path = repo_root / ".claude" / "settings.json"
    config = read_json(path)
    changed = merge_mcp_servers(config, servers)
    if changed:
        write_json(path, config)
    return changed


def register_claude_desktop(servers: dict) -> bool:
    """Register in Claude Desktop claude_desktop_config.json."""
    platform = sys.platform
    if platform == "darwin":
        path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif platform == "linux":
        path = Path.home() / ".config" / "claude" / "claude_desktop_config.json"
    elif platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        path = Path(appdata) / "Claude" / "claude_desktop_config.json"
    else:
        return False

    config = read_json(path)
    changed = merge_mcp_servers(config, servers)
    if changed:
        write_json(path, config)
    return changed


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    repo_root   = Path(__file__).resolve().parent.parent
    jarvis_home = os.environ.get("JARVIS_DATA_DIR",
                  os.environ.get("JARVIS_HOME",
                  str(Path.home() / "JARVIS")))
    node_bin    = find_node()
    servers     = build_server_entries(repo_root, jarvis_home, node_bin)

    changed_global  = register_claude_code_global(servers)
    changed_project = register_claude_code_project(repo_root, servers)
    changed_desktop = register_claude_desktop(servers)

    any_changed = changed_global or changed_project or changed_desktop

    if any_changed:
        targets = []
        if changed_global:  targets.append("~/.claude/settings.json")
        if changed_project: targets.append(".claude/settings.json")
        if changed_desktop: targets.append("Claude Desktop config")
        print(f"UPDATED: {', '.join(targets)}")
        print(f"  node: {node_bin}")
        print(f"  data: {jarvis_home}")
        print(f"  servers: {', '.join(servers.keys())}")
    else:
        print(f"already registered — node: {node_bin}, data: {jarvis_home}")


if __name__ == "__main__":
    main()
