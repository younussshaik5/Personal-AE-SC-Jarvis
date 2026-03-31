#!/usr/bin/env python3
"""
JARVIS v3 Universal Bootstrap
Platform-agnostic setup generator - fork-ready
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime


def create_portable_env_template(workspace_root: Path) -> Path:
    """Create .env template with platform-safe defaults"""
    env_template = workspace_root / ".env.template"
    
    content = f"""# JARVIS v3 Universal Configuration
# Copy this file to .env and customize for your system

# JARVIS data root - where all account data is stored
JARVIS_ROOT=${{HOME}}/JARVIS

# Current workspace root (auto-detected if not set)
WORKSPACE_ROOT={workspace_root}

# Platform (auto-detected: macos, linux, windows, wsl)
PLATFORM=

# NVIDIA API Key (required for AI processing)
# Get from: https://build.nvidia.com/
NVIDIA_API_KEY=

# Anthropic API Key (optional - fallback)
ANTHROPIC_API_KEY=

# JARVIS mode
JARVIS_MODE=autonomous
"""
    
    with open(env_template, 'w') as f:
        f.write(content)
    
    return env_template


def create_platform_config(workspace_root: Path, javis_root: Path) -> Path:
    """Create universal platform configuration"""
    config_dir = workspace_root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    config = {
        "version": "3.0.0",
        "generated": datetime.now().isoformat(),
        "workspace_root": str(workspace_root.resolve()),
        "jarvis_root": str(javis_root.resolve()),
        "platform": {
            "auto_detect": True,
            "supported": ["macos", "linux", "windows", "wsl"]
        },
        "paths": {
            "accounts_dir": "${JARVIS_ROOT}/ACCOUNTS",
            "logs_dir": "${JARVIS_ROOT}/logs",
            "data_dir": "${JARVIS_ROOT}/data",
            "temp_dir": "${JARVIS_ROOT}/data/cache"
        },
        "integration": {
            "claude_code": True,
            "claude_cowork": True,
            "opencode": True,
            "universal_bridge": True
        },
        "real_time_processing": {
            "enabled": True,
            "watchdog_enabled": True,
            "poll_interval": 2,
            "auto_skill_activation": True
        }
    }
    
    config_file = config_dir / "jarvis.universal.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config_file


def create_gitignore(workspace_root: Path) -> Path:
    """Create comprehensive .gitignore for forked repository"""
    gitignore_content = """# JARVIS v3 Universal - Gitignore
# Auto-generated - do not edit manually

# Environment and secrets
.env
.env.local
*.key
*.pem
secrets/

# Runtime directories
logs/
run/
instance/
tmp/
temp/

# Generated data (exclude from git)
JARVIS/data/
JARVIS/recordings/
JARVIS/cache/

# IDE and editor files
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*

# OS generated files
Thumbs.db
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
"""
    
    gitignore_path = workspace_root / ".gitignore"
    existing = set()
    
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            existing = set(f.read().splitlines())
    
    new_lines = [line for line in gitignore_content.splitlines() 
                 if line and line not in existing]
    
    if new_lines:
        with open(gitignore_path, 'a') as f:
            f.write('\n' + '\n'.join(new_lines) + '\n')
    
    return gitignore_path


def create_universal_startup(workspace_root: Path, javis_root: Path) -> Path:
    """Create universal startup script"""
    start_script = workspace_root / "start_jarvis.sh"
    
    script_content = f"""#!/bin/bash
# JARVIS v3 Universal Startup
# Works on macOS, Linux, Windows WSL
set -e

# Resolve paths
export WORKSPACE_ROOT="{workspace_root}"
export JARVIS_ROOT="{javis_root}"

echo "🚀 Starting JARVIS v3 Universal Bridge..."
echo "📁 Workspace: $WORKSPACE_ROOT"
echo "📁 JARVIS Root: $JARVIS_ROOT"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# Check dependencies
python3 -c "import watchdog, websockets" 2>/dev/null || {{
    echo "📦 Installing dependencies..."
    pip install -q -r requirements-universal.txt
}}

# Create necessary directories
mkdir -p "$JARVIS_ROOT"/{{ACCOUNTS,logs,data}}
mkdir -p "$WORKSPACE_ROOT"/{{.claude,.opencode}}

# Start universal bridge
echo "🔄 Enabling real-time intelligence..."
python3 -m jarvis.universal_bridge "$WORKSPACE_ROOT" &
BRIDGE_PID=$!

echo "✅ JARVIS is running (PID: $BRIDGE_PID)"
echo "📡 Monitoring Claude Code, OpenCode, and all conversations"
echo ""
echo "Commands:"
echo "  • Claude Desktop: 'list my accounts'"
echo "  • OpenCode: Workspace context active"
echo "  • Stop: kill $BRIDGE_PID"
echo ""
echo "Dashboard: $JARVIS_ROOT/logs/"

# Wait
wait $BRIDGE_PID
"""
    
    with open(start_script, 'w') as f:
        f.write(script_content)
    
    os.chmod(start_script, 0o755)
    return start_script


def create_docker_compose(workspace_root: Path) -> Path:
    """Create Docker Compose for containerized deployment"""
    docker_compose = workspace_root / "docker-compose.yml"
    
    content = """version: '3.8'

services:
  jarvis-bridge:
    image: python:3.11-slim
    working_dir: /workspace
    volumes:
      - .:/workspace
      - jarvis-data:/jarvis
    environment:
      - WORKSPACE_ROOT=/workspace
      - JARVIS_ROOT=/jarvis
      - NVIDIA_API_KEY=${NVIDIA_API_KEY:-}
      - PLATFORM=container
    command: >
      bash -c "
        pip install -q -r requirements-universal.txt &&
        python -m jarvis.universal_bridge /workspace
      "
    restart: unless-stopped
    stdin_open: true
    tty: true

volumes:
  jarvis-data:
"""
    
    with open(docker_compose, 'w') as f:
        f.write(content)
    
    return docker_compose


def create_universal_requirements() -> Path:
    """Create universal requirements - minimal, portable"""
    requirements = Path("requirements-universal.txt")
    
    content = """# JARVIS v3 Universal Dependencies
# Minimal, cross-platform requirements
watchdog>=4.0.0
pyyaml>=6.0
websockets>=12.0
"""
    
    with open(requirements, 'w') as f:
        f.write(content)
    
    return requirements


def create_github_workflows(workspace_root: Path) -> Path:
    """Create GitHub Actions CI for cross-platform testing"""
    workflows_dir = workspace_root / ".github" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    
    workflow = workflows_dir / "universal-test.yml"
    
    content = """name: JARVIS Universal Test

on:
  push:
    branches: [ main, master ]
  pull_request:

jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.11', '3.12']
    
    runs-on: ${{ matrix.os }}
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-universal.txt
    
    - name: Test universal detection
      run: |
        python -c "
        from jarvis.autodetect import UniversalWorkspaceDetector
        detector = UniversalWorkspaceDetector()
        context = detector.get_workspace_context()
        print('✓ Platform:', context.platform_name)
        print('✓ Workspace:', context.root)
        print('✓ Accounts:', len(context.accounts_found))
        assert context.root is not None
        assert context.platform_name in ['macos', 'linux', 'windows', 'wsl', 'unknown']
        print('✅ All checks passed')
        "
    
    - name: Test account resolver
      run: |
        python -c "
        from jarvis.account_resolver import SmartAccountResolver
        resolver = SmartAccountResolver()
        accounts = resolver.load_accounts()
        print(f'✓ Loaded {{len(accounts)}} accounts')
        print('✅ Account resolver ready')
        "
    
    - name: Test universal bridge
      run: |
        python -c "
        from jarvis.universal_bridge import RealtimeBridge
        bridge = RealtimeBridge()
        print('✓ Bridge initialized')
        print('✓ All modules importable')
        print('✅ Universal bridge ready')
        "
"""
    
    with open(workflow, 'w') as f:
        f.write(content)
    
    return workflow


def create_readme(workspace_root: Path, javis_root: Path) -> Path:
    """Create universal README for forkable repository"""
    readme = workspace_root / "README.md"
    
    content = f"""# JARVIS v3 Universal Intelligence Bridge

** Autonomous AI Sales Assistant that works across all your development environments **

[![Test Universal](https://github.com/yourusername/jarvis-universal/actions/workflows/universal-test.yml/badge.svg)](https://github.com/yourusername/jarvis-universal/actions/workflows/universal-test.yml)

## Features

- Universal Detection - Auto-detects any workspace with JARVIS data
- Real-time Processing - Skills update as you chat in Claude Code / OpenCode
- Cross-Platform - Works on macOS, Linux, Windows, WSL, Docker
- Zero Hard Paths - Fork and run anywhere
- Git-Friendly - Portable configuration, no local dependencies

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-fork>
cd jarvis-universal

# Run universal setup
./setup_jarvis_universal.sh
```

### 2. Start JARVIS

```bash
# From any workspace with JARVIS data
./start_jarvis.sh
```

JARVIS automatically:
- Detects your platform and adjusts paths
- Finds existing account data
- Starts real-time monitoring
- Enables skills in Claude Code / OpenCode

## Architecture

```
Workspace → Universal Bridge → Account Resolver → Skill Activator
            │
            ├── Claude Code (.claude/workspace.md)
            ├── OpenCode (.opencode/conversations.md)  
            ├── Manual inputs
            └── File drops (MEETINGS/, EMAILS/, DOCUMENTS/)
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `JARVIS_ROOT` | JARVIS data directory | `$HOME/JARVIS` |
| `WORKSPACE_ROOT` | Current workspace | Auto-detected |
| `NVIDIA_API_KEY` | NVIDIA API key | Required |
| `PLATFORM` | Platform type | Auto-detected |

### Platform Detection

JARVIS auto-detects:
- macOS (Darwin)
- Linux (various distros)
- Windows (WSL)
- Docker containers

## Project Structure

```
jarvis-universal/
├── jarvis/
│   ├── autodetect.py          # Universal workspace detection
│   ├── universal_bridge.py    # Real-time processing
│   ├── account_resolver.py    # Smart account detection
│   └── __init__.py
├── scripts/
│   └── setup_jarvis_universal.py  # Cross-platform setup
├── config/
│   └── jarvis.universal.json      # Auto-generated config
├── .claude/                  # Claude Code integration
├── .opencode/               # OpenCode integration
├── ACCOUNTS/                # Account data (symlink to JARVIS_ROOT)
├── start_jarvis.sh         # Universal startup
├── requirements-universal.txt
└── docker-compose.yml      # Container deployment
"""
    
    with open(readme, 'w') as f:
        f.write(content)
    
    return readme


def main():
    """Main bootstrap entry point"""
    workspace_root = Path.cwd()
    
    print("🚀 JARVIS v3 Universal Bootstrap")
    print("=" * 50)
    print(f"Workspace: {workspace_root}")
    
    # Determine JARVIS root
    javis_root_str = os.environ.get('JARVIS_ROOT', str(Path.home() / 'JARVIS'))
    javis_root = Path(javis_root_str)
    javis_root.mkdir(parents=True, exist_ok=True)
    
    print(f"JARVIS Root: {javis_root}")
    
    # Create all components
    print("\n📦 Generating portable configuration...")
    create_portable_env_template(workspace_root)
    print("  ✓ .env.template created")
    
    create_platform_config(workspace_root, javis_root)
    print("  ✓ config/jarvis.universal.json created")
    
    create_gitignore(workspace_root)
    print("  ✓ .gitignore updated")
    
    create_universal_startup(workspace_root, javis_root)
    print("  ✓ start_jarvis.sh created")
    
    create_docker_compose(workspace_root)
    print("  ✓ docker-compose.yml created")
    
    create_universal_requirements()
    print("  ✓ requirements-universal.txt created")
    
    create_github_workflows(workspace_root)
    print("  ✓ .github/workflows/universal-test.yml created")
    
    create_readme(workspace_root, javis_root)
    print("  ✓ README.md created")
    
    # Create ACCOUNTS symlink
    accounts_link = workspace_root / "ACCOUNTS"
    if not accounts_link.exists():
        accounts_link.symlink_to(javis_root / "ACCOUNTS")
        print(f"  ✓ ACCOUNTS → {javis_root}/ACCOUNTS")
    
    print("\n✅ Universal bootstrap complete!")
    print("\nNext steps:")
    print("  1. Copy .env.template to .env")
    print("  2. Add your NVIDIA_API_KEY")
    print("  3. Run: ./start_jarvis.sh")
    print("\n🎯 JARVIS is ready for autonomous operation!")


if __name__ == "__main__":
    main()