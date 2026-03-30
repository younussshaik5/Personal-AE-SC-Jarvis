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

# ── Detect Python 3.11+ ───────────────────────────────────
detect_python() {
  for candidate in python3.13 python3.12 python3.11 python3; do
    bin="$(command -v "$candidate" 2>/dev/null)"
    if [ -z "$bin" ]; then
      # Also try common install locations on macOS
      for prefix in /Library/Frameworks/Python.framework/Versions/3.13/bin \
                    /Library/Frameworks/Python.framework/Versions/3.12/bin \
                    /Library/Frameworks/Python.framework/Versions/3.11/bin \
                    /opt/homebrew/bin /usr/local/bin; do
        if [ -x "$prefix/$candidate" ]; then
          bin="$prefix/$candidate"
          break
        fi
      done
    fi
    if [ -n "$bin" ]; then
      minor=$("$bin" -c 'import sys; print(sys.version_info.minor)' 2>/dev/null)
      major=$("$bin" -c 'import sys; print(sys.version_info.major)' 2>/dev/null)
      if [ "$major" = "3" ] && [ "${minor:-0}" -ge 11 ] 2>/dev/null; then
        echo "$bin"
        return 0
      fi
    fi
  done
  return 1
}

PYTHON_BIN="$(detect_python)"
if [ -z "$PYTHON_BIN" ]; then
  echo -e "  ${YELLOW}⚠ Python 3.11+ not found — run ./setup.sh first${NC}"
  exit 1
fi
export PYTHON_BIN

# ── Detect Node.js ────────────────────────────────────────
detect_node() {
  # Prefer node in PATH first
  bin="$(command -v node 2>/dev/null)"
  if [ -n "$bin" ]; then echo "$bin"; return 0; fi

  # Common fixed locations (macOS + Linux)
  for candidate in /opt/homebrew/bin/node /usr/local/bin/node /usr/bin/node; do
    if [ -x "$candidate" ]; then echo "$candidate"; return 0; fi
  done

  # nvm — find highest version
  if [ -d "$HOME/.nvm/versions/node" ]; then
    bin=$(ls -1d "$HOME/.nvm/versions/node"/*/bin/node 2>/dev/null | sort -V | tail -1)
    if [ -n "$bin" ] && [ -x "$bin" ]; then echo "$bin"; return 0; fi
  fi

  return 1
}

NODE_BIN="$(detect_node)"
if [ -z "$NODE_BIN" ]; then
  echo -e "  ${YELLOW}⚠ Node.js not found — run ./setup.sh first${NC}"
  exit 1
fi
export NODE_BIN

# ── Check API key ─────────────────────────────────────────
if [ -f .env ]; then
  if grep -q "YOUR_NVIDIA_API_KEY_HERE" .env 2>/dev/null || \
     ! grep -q "^NVIDIA_API_KEY=.\+" .env 2>/dev/null; then
    echo -e "  ${YELLOW}⚠ NVIDIA_API_KEY not set in .env — LLM features will not work${NC}"
    echo "  Edit .env and add your key, or re-run ./setup.sh"
  fi
fi

# ── Auto-register MCP with Claude Desktop ─────────────────
# Runs every time so new machines get wired up automatically on first start.
if [ -f "scripts/register_mcp.py" ]; then
  REGISTER_OUT=$("$PYTHON_BIN" scripts/register_mcp.py 2>&1)
  if echo "$REGISTER_OUT" | grep -q "UPDATED"; then
    echo -e "  ${GREEN}✓ Claude Desktop MCP config updated — restart Claude if it was open${NC}"
  elif echo "$REGISTER_OUT" | grep -q "Registered\|already"; then
    echo -e "  ${GREEN}✓ Claude Desktop MCP already registered${NC}"
  else
    echo -e "  ${YELLOW}⚠ MCP registration: $REGISTER_OUT${NC}"
  fi
fi

# ── Ensure directories exist ──────────────────────────────
mkdir -p "$JARVIS_HOME"/{ACCOUNTS,MEMORY,data/meeting_queue,logs,recordings}

# ── Kill any existing JARVIS processes ────────────────────
for pidfile in .jarvis.pid .mcp_observer.pid .ui.pid; do
  if [ -f "$pidfile" ]; then
    PID=$(cat "$pidfile" 2>/dev/null)
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
      kill "$PID" 2>/dev/null || true
    fi
    rm -f "$pidfile"
  fi
done

# ── Start MCP Observer (if built) ─────────────────────────
if [ -d "mcp-opencode-observer/dist" ]; then
  echo ""
  echo "[1] Starting MCP Observer..."
  "$NODE_BIN" mcp-opencode-observer/dist/index.js > "$JARVIS_HOME/logs/observer.log" 2>&1 &
  echo $! > .mcp_observer.pid
  echo "    PID: $(cat .mcp_observer.pid)"
fi

# ── Start JARVIS Core Orchestrator ────────────────────────
echo ""
echo "[2] Starting JARVIS Core..."
"$PYTHON_BIN" -m jarvis.core.orchestrator > "$JARVIS_HOME/logs/orchestrator.log" 2>&1 &
echo $! > .jarvis.pid
echo "    PID: $(cat .jarvis.pid)"

# ── Start Dashboard UI ────────────────────────────────────
echo ""
echo "[3] Starting Dashboard..."
"$PYTHON_BIN" -m jarvis.ui.server > "$JARVIS_HOME/logs/dashboard.log" 2>&1 &
echo $! > .ui.pid
echo "    PID: $(cat .ui.pid)"

sleep 2

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   JARVIS is running!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "  Dashboard:    http://localhost:8080"
echo "  Python:       $PYTHON_BIN"
echo "  Node:         $NODE_BIN"
echo ""
echo "  Logs:"
echo "    tail -f $JARVIS_HOME/logs/orchestrator.log"
echo "    tail -f $JARVIS_HOME/logs/dashboard.log"
echo ""
echo "  To stop: ./stop_jarvis.sh"
echo ""
