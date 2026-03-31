# JARVIS v3 Universal Intelligence Bridge

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
