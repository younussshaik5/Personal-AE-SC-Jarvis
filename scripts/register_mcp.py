#!/usr/bin/env python3
"""
Register JARVIS MCP servers across ALL Claude interfaces.
Runs on every `start_jarvis.sh` — fully idempotent.

Targets:
  1. ~/.claude/settings.json                     — Claude Code CLI (global, any directory)
  2. <repo>/.claude/settings.json                — Claude Code project-level
  3. Claude Desktop claude_desktop_config.json   — Claude Desktop app + CoWork
  4. ~/.config/opencode/opencode.jsonc           — OpenCode (different format)
"""

import json
import os
import re
import shutil
import sys
from pathlib import Path


# ── Node detection ────────────────────────────────────────────────────────────

def find_node() -> str:
    """Return the full path to a usable node binary."""
    # 1. Passed in by start_jarvis.sh
    env = os.environ.get("NODE_BIN", "")
    if env and Path(env).exists():
        return env
    # 2. In PATH
    found = shutil.which("node")
    if found:
        return found
    # 3. Common fixed locations
    for c in ["/opt/homebrew/bin/node", "/usr/local/bin/node", "/usr/bin/node"]:
        if Path(c).exists():
            return c
    # 4. nvm highest version
    nvm = Path.home() / ".nvm" / "versions" / "node"
    if nvm.is_dir():
        for v in sorted(nvm.iterdir(), key=lambda p: p.name, reverse=True):
            node = v / "bin" / "node"
            if node.exists():
                return str(node)
    return "node"


# ── JSON / JSONC helpers ──────────────────────────────────────────────────────

def strip_jsonc_comments(text: str) -> str:
    """Strip // and /* */ comments from JSONC so json.loads can parse it."""
    # Remove block comments
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    # Remove line comments (but not URLs like https://)
    text = re.sub(r'(?<!:)//[^\n]*', '', text)
    return text


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        raw = path.read_text(encoding="utf-8")
        return json.loads(strip_jsonc_comments(raw))
    except (json.JSONDecodeError, IOError):
        return {}


def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ── Claude Code / Desktop format ──────────────────────────────────────────────
# Format: { "mcpServers": { "name": { "command": "node", "args": [...], "env": {...} } } }

def claude_servers(mcp_path: Path, observer_path: Path,
                   node: str, jarvis_home: str) -> dict:
    return {
        "jarvis": {
            "command": node,
            "args": [str(mcp_path)],
            "env": {"JARVIS_DATA_DIR": jarvis_home},
        },
        **({"jarvis-opencode-observer": {
            "command": node,
            "args": [str(observer_path)],
            "env": {
                "JARVIS_DATA_DIR": jarvis_home,
                "OPENCODE_OBSERVER_PORT": "3000",
                "OPENCODE_OBSERVER_WS_PORT": "3001",
            },
        }} if observer_path.exists() else {}),
    }


def register_claude_settings(path: Path, servers: dict) -> bool:
    config = read_json(path)
    existing = config.get("mcpServers", {})
    changed = any(existing.get(k) != v for k, v in servers.items())
    if changed:
        config["mcpServers"] = {**existing, **servers}
        write_json(path, config)
    return changed


def register_claude_desktop(servers: dict) -> bool:
    if sys.platform == "darwin":
        path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif sys.platform == "linux":
        path = Path.home() / ".config" / "claude" / "claude_desktop_config.json"
    elif sys.platform == "win32":
        path = Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json"
    else:
        return False
    return register_claude_settings(path, servers)


# ── OpenCode format ───────────────────────────────────────────────────────────
# Format: { "mcp": { "name": { "type": "local", "command": ["node", "path"], "enabled": true } } }

def opencode_servers(mcp_path: Path, observer_path: Path,
                     node: str, jarvis_home: str) -> dict:
    servers = {
        "jarvis": {
            "type": "local",
            "command": [node, str(mcp_path)],
            "enabled": True,
            "timeout": 30000,
            "env": {"JARVIS_DATA_DIR": jarvis_home},
        }
    }
    if observer_path.exists():
        servers["jarvis-opencode-observer"] = {
            "type": "local",
            "command": [node, str(observer_path)],
            "enabled": True,
            "timeout": 30000,
            "env": {
                "JARVIS_DATA_DIR": jarvis_home,
                "OPENCODE_OBSERVER_PORT": "3000",
                "OPENCODE_OBSERVER_WS_PORT": "3001",
            },
        }
    return servers


def register_opencode(servers: dict) -> bool:
    path = Path.home() / ".config" / "opencode" / "opencode.jsonc"
    if not path.exists():
        # Also check alternate location
        alt = Path.home() / ".opencode" / "config.json"
        if not alt.exists():
            return False
        path = alt

    config = read_json(path)
    existing_mcp = config.get("mcp", {})
    changed = any(existing_mcp.get(k) != v for k, v in servers.items())
    if changed:
        config["mcp"] = {**existing_mcp, **servers}
        # Write as JSONC (plain JSON is valid JSONC)
        path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return changed


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    repo_root   = Path(__file__).resolve().parent.parent
    jarvis_home = os.environ.get("JARVIS_DATA_DIR",
                  os.environ.get("JARVIS_HOME",
                  str(Path.home() / "JARVIS")))
    node        = find_node()

    mcp_path      = repo_root / "mcp-jarvis-server" / "dist" / "index.js"
    observer_path = repo_root / "mcp-opencode-observer" / "dist" / "index.js"

    # Claude Code / Desktop format
    cc_servers = claude_servers(mcp_path, observer_path, node, jarvis_home)
    # OpenCode format
    oc_servers = opencode_servers(mcp_path, observer_path, node, jarvis_home)

    results = {
        "~/.claude/settings.json":    register_claude_settings(Path.home() / ".claude" / "settings.json", cc_servers),
        ".claude/settings.json":      register_claude_settings(repo_root / ".claude" / "settings.json", cc_servers),
        "Claude Desktop":             register_claude_desktop(cc_servers),
        "OpenCode":                   register_opencode(oc_servers),
    }

    updated = [k for k, v in results.items() if v]
    if updated:
        print(f"UPDATED: {', '.join(updated)}")
    else:
        print("already registered")

    print(f"  node: {node}")
    print(f"  data: {jarvis_home}")
    servers_list = list(cc_servers.keys())
    print(f"  servers: {', '.join(servers_list)}")


if __name__ == "__main__":
    main()
