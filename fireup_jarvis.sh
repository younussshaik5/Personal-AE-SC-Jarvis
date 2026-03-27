#!/bin/bash
# JARVIS Complete Launch Script
# One-command startup: fires up MCP observer, JARVIS core, and UI dashboard

set -e

echo "═══════════════════════════════════════════════════════════"
echo "   J.A.R.V.I.S. - Autonomous AI Employee"
echo "   Complete System Startup"
echo "═══════════════════════════════════════════════════════════"
echo ""

cd "$(dirname "$0")"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a process is running
is_running() {
    pgrep -f "$1" > /dev/null
}

# Function to start a process
start_process() {
    local name="$1"
    local cmd="$2"
    local pid_file="$3"
    
    echo -e "${BLUE}[$name]${NC} Starting..."
    
    if is_running "$name"; then
        echo -e "${GREEN}[$name]${NC} Already running"
        return 0
    fi
    
    # Execute command in background
    eval "$cmd" > "logs/${name}.log" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"
    
    # Wait a moment and check if it's still running
    sleep 2
    if ps -p $pid > /dev/null; then
        echo -e "${GREEN}[$name]${NC} Started (PID $pid)"
        return 0
    else
        echo -e "${YELLOW}[$name]${NC} Failed to start, check logs/${name}.log"
        return 1
    fi
}

# 1. MCP Observer
echo -e "\n${BLUE}Step 1/3:${NC} Starting MCP Observer (Node.js)..."
if [ ! -f "mcp-opencode-observer/dist/index.js" ]; then
    echo "  Building MCP observer..."
    (cd mcp-opencode-observer && npm install > /dev/null 2>&1 && npm run build) || {
        echo "  ❌ MCP build failed"
        exit 1
    }
fi

# Ensure MCP config exists at expected path (workspace root/config/mcp-observer.json)
mkdir -p config
if [ ! -f "config/mcp-observer.json" ]; then
    echo "  Copying MCP observer config to workspace root..."
    cp mcp-opencode-observer/config/mcp-observer.json config/mcp-observer.json
fi

start_process "mcp_observer" \
    "node mcp-opencode-observer/dist/index.js" \
    ".mcp_observer.pid"

# 2. JARVIS Core
echo -e "\n${BLUE}Step 2/3:${NC} Starting JARVIS Core (Python)..."

# Install Python package if needed
if ! python3 -c "import jarvis" 2>/dev/null; then
    echo "  Installing JARVIS Python package..."
    pip install -e jarvis > /dev/null 2>&1
fi

# Create config if doesn't exist
if [ ! -f "jarvis/config/jarvis.yaml" ]; then
    echo "  Running first-time setup..."
    python3 jarvis/scripts/setup.py --silent || true
fi

# Ensure data directories
mkdir -p jarvis/data/{personas,patterns,archives,cache,history}
mkdir -p logs/{audit,errors,performance}

start_process "jarvis_core" \
    "python3 -m jarvis.core.orchestrator" \
    ".jarvis.pid"

# 3. UI Dashboard
echo -e "\n${BLUE}Step 3/3:${NC} Starting JARVIS UI Dashboard..."

# Install UI dependencies
if ! python3 -c "import http.server" 2>/dev/null; then
    echo "  Note: Python http.server should be available"
fi

start_process "jarvis_ui" \
    "python3 -m jarvis.ui.server" \
    ".ui.pid"

# All started
echo ""
echo "═══════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ JARVIS SYSTEM IS ONLINE${NC}"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Components running:"
echo "  • MCP Observer   → Polling OpenCode DB (pid $(cat .mcp_observer.pid 2>/dev/null || echo N/A))"
echo "  • JARVIS Core    → Python orchestrator (pid $(cat .jarvis.pid 2>/dev/null || echo N/A))"
echo "  • UI Dashboard   → http://localhost:8080 (pid $(cat .ui.pid 2>/dev/null || echo N/A))"
echo ""
echo "Quick access:"
echo "  🌐 Dashboard:    http://localhost:8080"
echo "  📊 Status:       jarvis status"
echo "  📋 Monitor:      jarvis monitor --live"
echo "  👤 Personas:     jarvis persona list"
echo "  💬 Events tail:  tail -f logs/jarvis.log"
echo ""
echo "To stop all:"
echo "  pkill -f mcp-opencode-observer"
echo "  pkill -f jarvis.core.orchestrator"
echo "  pkill -f jarvis.ui.server"
echo ""