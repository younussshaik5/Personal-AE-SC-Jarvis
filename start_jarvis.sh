#!/bin/bash
# JARVIS v2 - Start all services locally

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

JARVIS_HOME="${JARVIS_HOME:-$HOME/Documents/claude space/JARVIS}"
export JARVIS_HOME
export JARVIS_DATA_DIR="$JARVIS_HOME"

echo "============================================"
echo "  Starting JARVIS v2"
echo "  Data: $JARVIS_HOME"
echo "============================================"

# Ensure directories exist
mkdir -p "$JARVIS_HOME"/{ACCOUNTS,MEMORY,data/meeting_queue,logs,recordings}

# Start MCP Observer (if opencode/claude db exists)
if [ -d "mcp-opencode-observer/dist" ]; then
    echo "[1] Starting MCP Observer..."
    node mcp-opencode-observer/dist/index.js > "$JARVIS_HOME/logs/observer.log" 2>&1 &
    echo $! > .mcp_observer.pid
    echo "  PID: $(cat .mcp_observer.pid)"
fi

# Start JARVIS Core Orchestrator
echo "[2] Starting JARVIS Core..."
python3 -m jarvis.core.orchestrator > "$JARVIS_HOME/logs/orchestrator.log" 2>&1 &
echo $! > .jarvis.pid
echo "  PID: $(cat .jarvis.pid)"

# Start Dashboard UI
echo "[3] Starting Dashboard..."
python3 -m jarvis.ui.server > "$JARVIS_HOME/logs/dashboard.log" 2>&1 &
echo $! > .ui.pid
echo "  PID: $(cat .ui.pid)"

sleep 2

echo ""
echo "============================================"
echo "  JARVIS is running!"
echo "============================================"
echo ""
echo "  Dashboard: http://localhost:8080"
echo "  Claude Desktop: JARVIS MCP server ready"
echo ""
echo "  Logs:"
echo "    tail -f $JARVIS_HOME/logs/orchestrator.log"
echo "    tail -f $JARVIS_HOME/logs/dashboard.log"
echo ""
echo "  To stop: ./stop_jarvis.sh"
echo ""
