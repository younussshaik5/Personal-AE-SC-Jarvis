#!/usr/bin/env python3
"""
JARVIS — Fix Claude Desktop MCP Config
Run this once to register JARVIS in Claude Desktop, then restart Claude Desktop.
"""

import os
import sys
import json
import shutil
from pathlib import Path

# Add project to path for PlatformUtils import
sys.path.insert(0, str(Path(__file__).parent))
from jarvis_mcp.platform_utils import PlatformUtils

# ── 1. Locate the Claude Desktop config file ──────────────────────────────
if sys.platform == "win32":
    appdata = os.environ.get("APPDATA", "")
    config_path = Path(appdata) / "Claude" / "claude_desktop_config.json"
elif sys.platform == "darwin":
    config_path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
else:
    config_path = Path.home() / ".config" / "Claude" / "claude_desktop_config.json"

# ── 2. Locate JARVIS project root (same folder as this script) ────────────
project_path = Path(__file__).parent.resolve()
server_script = project_path / "jarvis_mcp_server.py"
crm_script    = project_path / "crm_sidecar.py"
accounts_path = project_path / "ACCOUNTS"

if not server_script.exists():
    print(f"❌  Cannot find {server_script}")
    print("    Make sure you're running this from inside the JARVIS project folder.")
    input("\nPress Enter to exit...")
    sys.exit(1)

# ── 3. Find Python executable ─────────────────────────────────────────────
python_exe = sys.executable  # same Python that's running THIS script

# ── 4. Load existing config (or start fresh) ─────────────────────────────
config_path.parent.mkdir(parents=True, exist_ok=True)

if config_path.exists():
    # Back up before touching it
    backup = config_path.with_suffix(".json.bak")
    shutil.copy2(config_path, backup)
    print(f"📋  Backed up existing config → {backup.name}")
    with open(config_path, "r", encoding="utf-8") as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError:
            print("⚠️   Existing config was invalid JSON — starting fresh.")
            config = {}
else:
    print(f"📄  No config found at {config_path} — creating new one.")
    config = {}

# ── 5. Inject JARVIS MCP entries ──────────────────────────────────────────
config.setdefault("mcpServers", {})

config["mcpServers"]["jarvis"] = {
    "command": python_exe,
    "args": [PlatformUtils.normalize_path(server_script)],
    "disabled": False
}

if crm_script.exists():
    config["mcpServers"]["jarvis-crm"] = {
        "command": python_exe,
        "args": [PlatformUtils.normalize_path(crm_script)],
        "disabled": False
    }

# ── 6. Add JARVIS folder to trusted folders (normalize paths for portability) ─
config.setdefault("preferences", {})
config["preferences"].setdefault("localAgentModeTrustedFolders", [])
for p in [project_path, accounts_path]:
    p_normalized = PlatformUtils.normalize_path(p)
    if p_normalized not in config["preferences"]["localAgentModeTrustedFolders"]:
        config["preferences"]["localAgentModeTrustedFolders"].append(p_normalized)

# ── 7. Write updated config ───────────────────────────────────────────────
with open(config_path, "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2)

# ── 8. Verify ─────────────────────────────────────────────────────────────
print()
print("╔══════════════════════════════════════════════════╗")
print("║           ✅  JARVIS Config Fixed!               ║")
print("╚══════════════════════════════════════════════════╝")
print()
print(f"  Config  : {config_path}")
print(f"  Python  : {python_exe}")
print(f"  Server  : {server_script}")
print()
print("  MCP entries registered:")
for name, entry in config["mcpServers"].items():
    marker = "✅" if name in ("jarvis", "jarvis-crm") else "  "
    print(f"    {marker}  {name}")
print()
print("  ⚡ Next step: QUIT Claude Desktop (Ctrl+Q) and reopen it.")
print("     JARVIS tools will appear in the 🔨 Tools panel.")
print()
input("Press Enter to exit...")
