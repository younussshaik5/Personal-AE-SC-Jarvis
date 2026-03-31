#!/bin/bash
# JARVIS v3 Universal Startup
# Works on macOS, Linux, Windows WSL
set -e

# Resolve paths dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export WORKSPACE_ROOT="${WORKSPACE_ROOT:-$SCRIPT_DIR}"
export JARVIS_ROOT="${JARVIS_ROOT:-$HOME/JARVIS}"

echo "🚀 Starting JARVIS v3 Universal Bridge..."
echo "📁 Workspace: $WORKSPACE_ROOT"
echo "📁 JARVIS Root: $JARVIS_ROOT"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# Check dependencies
python3 -c "import watchdog, websockets" 2>/dev/null || {
    echo "📦 Installing dependencies..."
    pip install -q -r requirements-universal.txt
}

# Create necessary directories
mkdir -p "$JARVIS_ROOT"/{ACCOUNTS,logs,data}
mkdir -p "$WORKSPACE_ROOT"/{.claude,.opencode}

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
