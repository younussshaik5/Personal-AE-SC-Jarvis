#!/bin/bash
# JARVIS v3 Universal Startup
# Works on macOS, Linux, Windows WSL
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
export WORKSPACE_ROOT="$SCRIPT_DIR"

# Colors
if [ -t 1 ]; then
  GREEN='\033[0;32m' BLUE='\033[0;34m' YELLOW='\033[1;33m' RED='\033[0;31m' NC='\033[0m'
else
  GREEN='' BLUE='' YELLOW='' RED='' NC=''
fi

# Load .env if exists
if [ -f .env ]; then
  set -a
  . .env
  set +a
fi

# Set JARVIS_HOME if not set
: "${JARVIS_HOME:=$HOME/JARVIS}"
export JARVIS_HOME
export JARVIS_DATA_DIR="$JARVIS_HOME"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   J.A.R.V.I.S. v3 — Starting${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo "  Workspace: $WORKSPACE_ROOT"
echo "  Data: $JARVIS_HOME"

# Check Python
if ! command -v python3 &> /dev/null; then
  echo -e "  ${RED}❌ Python 3 not found${NC}"
  exit 1
fi
echo "  ✓ Python: $(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"

# Check Node
if ! command -v node &> /dev/null; then
  echo -e "  ${YELLOW}⚠ Node.js not found — MCP tools disabled${NC}"
  NODE_BIN=""
else
  NODE_BIN="$(command -v node)"
  echo "  ✓ Node: $($NODE_BIN -v 2>/dev/null || echo 'unknown')"
fi

# Check NVIDIA API key
if [ -z "$NVIDIA_API_KEY" ]; then
  echo -e "  ${YELLOW}⚠ NVIDIA_API_KEY not set — LLM features limited${NC}"
else
  echo "  ✓ NVIDIA API key configured"
fi

# Create necessary directories
mkdir -p "$JARVIS_HOME"/{ACCOUNTS,logs,data}
mkdir -p "$WORKSPACE_ROOT"/{.claude,.opencode}
echo "  ✓ Directories ready"

# Register MCP with Claude Desktop / OpenCode
if [ -n "$NODE_BIN" ]; then
  echo ""
  echo "🔧 Registering MCP server..."
  export NODE_BIN
  python3 scripts/register_mcp.py || true
fi

# Stop any existing JARVIS processes
echo ""
echo "🔒 Stopping any existing JARVIS processes..."
pkill -f "jarvis.universal_bridge" 2>/dev/null || true
pkill -f "mcp-server" 2>/dev/null || true

# Start Universal Bridge
echo ""
echo "🚀 Starting Universal Intelligence Bridge..."
nohup python3 -m jarvis.universal_bridge > "$JARVIS_HOME/logs/universal_bridge.log" 2>&1 &
echo $! > .jarvis_bridge.pid
echo "  ✓ Bridge PID: $(cat .jarvis_bridge.pid)"

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   JARVIS v3 is running!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "📁 Workspace: $WORKSPACE_ROOT"
echo "📁 JARVIS Data: $JARVIS_HOME"
echo ""
echo "Universal Bridge running → real-time conversation processing"
echo ""
echo "Claude Desktop / Claude Code / OpenCode:"
echo "  • MCP tools registered (restart Claude if open)"
echo "  • Auto-detects account folders in ACCOUNTS/"
echo "  • Skills fire automatically on chat"
echo ""
echo "Logs: tail -f $JARVIS_HOME/logs/universal_bridge.log"
echo ""
echo "To stop: kill $(cat .jarvis_bridge.pid) 2>/dev/null || true"
echo ""