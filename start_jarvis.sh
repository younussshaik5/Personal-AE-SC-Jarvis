#!/bin/bash
# JARVIS v2 — Start all services
# Run ./setup.sh first if this is your first time.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
if [ -t 1 ]; then
  GREEN='\033[0;32m' BLUE='\033[0;34m' YELLOW='\033[1;33m' NC='\033[0m'
else
  GREEN='' BLUE='' YELLOW='' NC=''
fi

# Load environment from .env
if [ -f .env ]; then
  set -a
  . .env
  set +a
fi

# JARVIS_HOME must be set (by .env or environment)
if [ -z "$JARVIS_HOME" ]; then
  JARVIS_HOME="$HOME/JARVIS"
fi
JARVIS_HOME="${JARVIS_HOME/#\~/$HOME}"
export JARVIS_HOME
export JARVIS_DATA_DIR="$JARVIS_HOME"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   J.A.R.V.I.S. v2 — Starting${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo "  Data: $JARVIS_HOME"

# Check if .env has API keys
if [ -f .env ]; then
  if grep -q "YOUR_NVIDIA_API_KEY_HERE" .env 2>/dev/null || \
     ! grep -q "^NVIDIA_API_KEY=.\+" .env 2>/dev/null; then
    echo -e "  ${YELLOW}⚠ NVIDIA_API_KEY not set in .env — LLM features will not work${NC}"
    echo "  Edit .env and add your key, or re-run ./setup.sh"
  fi
fi

# Ensure directories exist
mkdir -p "$JARVIS_HOME"/{ACCOUNTS,MEMORY,data/meeting_queue,logs,recordings}

# Kill any existing JARVIS processes
for pidfile in .jarvis.pid .mcp_observer.pid .ui.pid; do
  if [ -f "$pidfile" ]; then
    PID=$(cat "$pidfile" 2>/dev/null)
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
      kill "$PID" 2>/dev/null || true
    fi
    rm -f "$pidfile"
  fi
done

# Start MCP Observer (if built)
if [ -d "mcp-opencode-observer/dist" ]; then
  echo ""
  echo "[1] Starting MCP Observer..."
  node mcp-opencode-observer/dist/index.js > "$JARVIS_HOME/logs/observer.log" 2>&1 &
  echo $! > .mcp_observer.pid
  echo "    PID: $(cat .mcp_observer.pid)"
fi

# Start JARVIS Core Orchestrator
echo ""
echo "[2] Starting JARVIS Core..."
python3 -m jarvis.core.orchestrator > "$JARVIS_HOME/logs/orchestrator.log" 2>&1 &
echo $! > .jarvis.pid
echo "    PID: $(cat .jarvis.pid)"

# Start Dashboard UI
echo ""
echo "[3] Starting Dashboard..."
python3 -m jarvis.ui.server > "$JARVIS_HOME/logs/dashboard.log" 2>&1 &
echo $! > .ui.pid
echo "    PID: $(cat .ui.pid)"

sleep 2

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   JARVIS is running!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "  Dashboard: http://localhost:8080"
echo "  Claude Desktop: JARVIS MCP ready"
echo ""
echo "  Logs:"
echo "    tail -f $JARVIS_HOME/logs/orchestrator.log"
echo "    tail -f $JARVIS_HOME/logs/dashboard.log"
echo ""
echo "  To stop: ./stop_jarvis.sh"
echo ""
