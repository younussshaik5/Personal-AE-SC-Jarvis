#!/usr/bin/env python3
"""JARVIS Setup Wizard - Configures and validates the installation."""

import sys
from pathlib import Path

# Ensure we can import jarvis package from workspace root
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import yaml
import subprocess
from jarvis.utils.logger import JARVISLogger

logger = JARVISLogger("setup")


def main():
    print("\n" + "="*60)
    print("   JARVIS SETUP WIZARD")
    print("="*60 + "\n")

    workspace = Path.cwd()
    print(f"Workspace: {workspace}")

    # 1. Verify OpenCode config
    config_paths = [
        Path.home() / ".config/opencode/opencode.jsonc",
        Path.home() / ".local/share/opencode/opencode.json",
        Path.home() / "Library/Application Support/Accomplish/opencode/opencode.json"
    ]
    opencode_config = None
    for p in config_paths:
        if p.exists():
            opencode_config = p
            print(f"✅ Found OpenCode config: {p}")
            break

    if not opencode_config:
        print("❌ OpenCode config not found. Please install OpenCode first.")
        return

    # 2. Check MCP observer built
    mcp_binary = workspace / "mcp-opencode-observer" / "dist" / "index.js"
    if not mcp_binary.exists():
        print("\nBuilding MCP observer...")
        subprocess.run(["npm", "install"], cwd="mcp-opencode-observer", check=False)
        subprocess.run(["npm", "run", "build"], cwd="mcp-opencode-observer", check=False)
        if mcp_binary.exists():
            print("✅ MCP observer built")
        else:
            print("❌ MCP observer build failed")
            return
    else:
        print("✅ MCP observer binary exists")

    # 3. Update OpenCode config with JARVIS MCP
    print("\nAdding JARVIS to OpenCode MCP configuration...")
    try:
        with open(opencode_config) as f:
            config_content = f.read()
        # Parse JSONC (strip comments)
        json_str = '\n'.join([l for l in config_content.splitlines() if not l.strip().startswith('//')])
        config = json.loads(json_str)

        config.setdefault("mcp", {})["jarvis"] = {
            "type": "local",
            "command": ["node", str(mcp_binary)],
            "enabled": True,
            "timeout": 30000
        }

        # Write back
        with open(opencode_config, "w") as f:
            json.dump(config, f, indent=2)
        print("✅ Updated OpenCode config")
    except Exception as e:
        print(f"❌ Failed to update config: {e}")

    # 4. Create JARVIS config
    jarvis_config_dir = workspace / "jarvis" / "config"
    jarvis_config_dir.mkdir(parents=True, exist_ok=True)
    jarvis_config_file = jarvis_config_dir / "jarvis.yaml"

    if not jarvis_config_file.exists():
        config_data = {
            "workspace_root": str(workspace),
            "data_dir": str(workspace / "jarvis" / "data"),
            "logs_dir": str(workspace / "jarvis" / "logs"),
            "approval_required": True,
            "approval_threshold": 50,
            "evolution": {
                "enabled": True,
                "cycle_interval_hours": 6
            },
            "archiving": {
                "enabled": True,
                "daily_snapshot": True,
                "retention_days": 90
            },
            "persona": {
                "default": "work",
                "auto_switch": True
            }
        }
        with open(jarvis_config_file, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
        print(f"✅ Created JARVIS config: {jarvis_config_file}")
    else:
        print(f"✅ JARVIS config already exists")

    # 5. Initialize data directories
    data_dirs = [
        workspace / "jarvis" / "data" / "personas",
        workspace / "jarvis" / "data" / "patterns",
        workspace / "jarvis" / "data" / "archives",
        workspace / "jarvis" / "data" / "cache",
        workspace / "jarvis" / "data" / "history",
        workspace / "jarvis" / "logs" / "audit",
        workspace / "jarvis" / "logs" / "errors",
        workspace / "jarvis" / "logs" / "performance"
    ]
    for d in data_dirs:
        d.mkdir(parents=True, exist_ok=True)
    print(f"✅ Created data directories ({len(data_dirs)})")

    # 6. Create default persona
    from jarvis.persona.persona_manager import PersonaManager, Persona
    from jarvis.utils.config import ConfigManager
    config_mgr = ConfigManager()
    config_mgr.config.workspace_root = workspace
    config_mgr.config.ensure_dirs()

    persona_mgr = PersonaManager(config_mgr.config, None)
    # Manually create if not exists
    personas_file = config_mgr.config.personas_dir / "personas.json"
    if not personas_file.exists():
        default_persona = Persona(
            id="work",
            name="Work",
            persona_type="solution_consultant",
            workspaces=[str(workspace)]
        )
        config_mgr.config.personas_dir.mkdir(parents=True, exist_ok=True)
        with open(personas_file, "w") as f:
            json.dump({"personas": [default_persona.__dict__], "last_updated": default_persona.created_at}, f, indent=2)
        print("✅ Created default persona 'work'")

    # 7. Summary
    print("\n" + "="*60)
    print("   SETUP COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("  1. Restart OpenCode to launch JARVIS")
    print("  2. Verify: jarvis status")
    print("  3. Customize: edit jarvis/config/jarvis.yaml")
    print("  4. Monitor: jarvis monitor --live")
    print("\nDocs:")
    print("  - JARVIS_README_GITHUB.md (comprehensive guide)")
    print("  - jarvis/docs/architecture.md (deep dive)")
    print("\nEnjoy your AI employee! 🤖")
    print()


if __name__ == "__main__":
    main()