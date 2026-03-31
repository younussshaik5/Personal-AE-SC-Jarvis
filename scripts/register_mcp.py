#!/usr/bin/env python3
"""
JARVIS v3 Universal MCP Registration
Registers portable MCP server with Claude Desktop & OpenCode
No hard paths - uses environment variables and relative paths
"""

import json
import os
import sys
from pathlib import Path

def find_node() -> str:
    """Find node binary"""
    node = os.environ.get("NODE_BIN")
    if node and Path(node).exists():
        return node
    # Try common locations
    for candidate in ["node", "/opt/homebrew/bin/node", "/usr/local/bin/node", "/usr/bin/node"]:
        if Path(candidate).exists() or os.which(candidate):
            return candidate
    return "node"

def get_mcp_server_path() -> Path:
    """Get path to built MCP server (returns dist/index.js)"""
    repo_root = Path(__file__).resolve().parent.parent
    mcp_dist = repo_root / "mcp-server" / "dist" / "index.js"
    if mcp_dist.exists():
        return mcp_dist
    # If not built, point to src
    return repo_root / "mcp-server" / "src" / "index.ts"

def get_claude_config_path() -> Path:
    """Find Claude Desktop config based on platform"""
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library/Application Support/Claude/claude_desktop_config.json"
    elif sys.platform == "linux":
        return home / ".config/Claude/claude_desktop_config.json"
    elif sys.platform == "win32":
        return Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json"
    else:
        return None

def load_json(path: Path) -> dict:
    """Load JSON file (return {} if missing/invalid)"""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except:
        return {}

def save_json(path: Path, data: dict):
    """Save JSON with proper formatting"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")

def register_claude_desktop(mcp_path: Path, node: str, env_vars: dict) -> bool:
    """Register with Claude Desktop (macOS app + CoWork)"""
    config_path = get_claude_config_path()
    if not config_path:
        print("⚠️ Claude Desktop config not found")
        return False

    config = load_json(config_path)
    if 'mcpServers' not in config:
        config['mcpServers'] = {}

    # Build server config
    server_config = {
        "command": node,
        "args": [str(mcp_path)],
        "env": env_vars,
        "autoAccept": True
    }

    # Check if changed
    existing = config['mcpServers'].get('jarvis')
    if existing != server_config:
        config['mcpServers']['jarvis'] = server_config
        save_json(config_path, config)
        print(f"✅ Registered JARVIS MCP with Claude Desktop")
        print(f"   Restart Claude to activate")
        return True
    return False

def register_claude_code_project(mcp_path: Path, node: str, env_vars: dict) -> bool:
    """Register project-level Claude Code (repo/.claude/settings.json)"""
    repo_root = Path(__file__).resolve().parent.parent
    project_config = repo_root / ".claude" / "settings.json"
    
    config = load_json(project_config)
    if 'mcpServers' not in config:
        config['mcpServers'] = {}
    
    server_config = {
        "command": node,
        "args": [str(mcp_path)],
        "env": env_vars
    }
    
    existing = config['mcpServers'].get('jarvis')
    if existing != server_config:
        config['mcpServers']['jarvis'] = server_config
        save_json(project_config, config)
        print(f"✅ Registered project-level Claude Code")
        return True
    return False

def register_opencode(mcp_path: Path, node: str, env_vars: dict) -> bool:
    """Register with OpenCode (JSONC format)"""
    # Check multiple possible OpenCode config locations
    home = Path.home()
    possible_paths = [
        home / ".config" / "opencode" / "opencode.jsonc",
        home / ".config" / "opencode" / "config.json",
        home / ".opencode" / "config.json",
    ]
    
    config_path = None
    for path in possible_paths:
        if path.exists():
            config_path = path
            break
    
    if not config_path:
        print("⚠️ OpenCode config not found (install OpenCode first)")
        return False
    
    config = load_json(config_path)
    if 'mcp' not in config:
        config['mcp'] = {}
    
    # OpenCode format differs slightly
    server_config = {
        "type": "local",
        "command": [node, str(mcp_path)],
        "env": env_vars,
        "enabled": True,
        "timeout": 30000
    }
    
    existing = config['mcp'].get('jarvis')
    if existing != server_config:
        config['mcp']['jarvis'] = server_config
        save_json(config_path, config)
        print(f"✅ Registered JARVIS MCP with OpenCode")
        print(f"   Restart OpenCode to activate")
        return True
    return False

def main():
    repo_root = Path(__file__).resolve().parent.parent
    mcp_path = get_mcp_server_path()
    node = find_node()
    
    # Environment variables - all dynamic
    env_vars = {
        "JARVIS_ROOT": os.environ.get("JARVIS_HOME", str(Path.home() / "JARVIS")),
        "WORKSPACE_ROOT": os.environ.get("WORKSPACE_ROOT", str(repo_root)),
        "PLATFORM": os.environ.get("PLATFORM", ""),
        "NVIDIA_API_KEY": os.environ.get("NVIDIA_API_KEY", "")
    }
    
    print("🔧 JARVIS v3 Universal MCP Registration")
    print(f"  MCP Server: {mcp_path}")
    print(f"  Workspace: {env_vars['WORKSPACE_ROOT']}")
    print(f"  JARVIS Root: {env_vars['JARVIS_ROOT']}")
    
    # Register with all interfaces
    updated_desktop = register_claude_desktop(mcp_path, node, env_vars)
    updated_project = register_claude_code_project(mcp_path, node, env_vars)
    updated_opencode = register_opencode(mcp_path, node, env_vars)
    
    if not (updated_desktop or updated_project or updated_opencode):
        print("✓ MCP already registered (no changes)")
    else:
        print("\n🎯 Ready! Claude Desktop, Claude Code, and OpenCode can now use JARVIS.")
    
    # Print summary
    print("\n📋 Registration Summary:")
    print("  • Claude Desktop: ✓" if updated_desktop else "  • Claude Desktop: already")
    print("  • Claude Code (project): ✓" if updated_project else "  • Claude Code (project): already")
    print("  • OpenCode: ✓" if updated_opencode else "  • OpenCode: already or not installed")

if __name__ == "__main__":
    main()