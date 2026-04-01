#!/bin/bash
# JARVIS MCP Setup — run once after cloning
# Usage: bash setup.sh

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

echo ""
echo "═══════════════════════════════════════════"
echo "  JARVIS MCP — Auto Setup"
echo "═══════════════════════════════════════════"
echo ""

# ── 1. Find Python 3.10+ ────────────────────────────────────────────────────
PYTHON=""
for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" &>/dev/null; then
        VER=$("$candidate" -c "import sys; print(sys.version_info.major * 10 + sys.version_info.minor)")
        if [ "$VER" -ge 310 ]; then
            PYTHON=$(command -v "$candidate")
            echo "✅ Found Python: $PYTHON ($("$PYTHON" --version))"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "❌ Python 3.10+ not found. Install via: brew install python@3.13"
    exit 1
fi

# ── 2. Install mcp SDK ───────────────────────────────────────────────────────
echo ""
echo "📦 Installing MCP SDK…"
"$PYTHON" -m pip install mcp --quiet 2>&1 | grep -E "(Successfully|already|ERROR)" || true
echo "✅ MCP SDK ready"

# ── 3. Install other dependencies ───────────────────────────────────────────
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    echo ""
    echo "📦 Installing project requirements…"
    "$PYTHON" -m pip install -r "$PROJECT_DIR/requirements.txt" --quiet 2>&1 | grep -E "(Successfully|already|ERROR)" || true
    echo "✅ Requirements installed"
fi

# ── 4. Create ACCOUNTS folder ───────────────────────────────────────────────
ACCOUNTS_DIR="$HOME/Documents/claude space/ACCOUNTS"
mkdir -p "$ACCOUNTS_DIR"
echo "✅ ACCOUNTS folder: $ACCOUNTS_DIR"

# ── 5. Register in Claude Desktop ───────────────────────────────────────────
echo ""
echo "⚙️  Configuring Claude Desktop…"

mkdir -p "$(dirname "$CLAUDE_CONFIG")"

# Read existing config or create fresh one
if [ -f "$CLAUDE_CONFIG" ]; then
    EXISTING=$(cat "$CLAUDE_CONFIG")
else
    EXISTING='{"mcpServers":{},"preferences":{}}'
fi

# Inject/overwrite the jarvis entry using Python
"$PYTHON" - <<PYEOF
import json, sys

config_path = "$CLAUDE_CONFIG"
project_path = "$PROJECT_DIR"
python_path = "$PYTHON"

try:
    with open(config_path) as f:
        config = json.load(f)
except:
    config = {"mcpServers": {}, "preferences": {}}

if "mcpServers" not in config:
    config["mcpServers"] = {}

config["mcpServers"]["jarvis"] = {
    "command": python_path,
    "args": [f"{project_path}/jarvis_mcp_server.py"],
    "disabled": False
}

with open(config_path, "w") as f:
    json.dump(config, f, indent=2)

print(f"✅ Registered JARVIS in Claude Desktop config")
print(f"   Python: {python_path}")
print(f"   Script: {project_path}/jarvis_mcp_server.py")
PYEOF

# ── 6. Quick smoke test ──────────────────────────────────────────────────────
echo ""
echo "🧪 Running smoke test…"
"$PYTHON" -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')
from jarvis_mcp.mcp_server import JarvisServer
s = JarvisServer()
print(f'✅ JARVIS boots — {len(s.skills)} skills loaded')
" 2>&1 | grep -E "(✅|❌|Error|skills)"

echo ""
echo "═══════════════════════════════════════════"
echo "  Setup complete!"
echo "═══════════════════════════════════════════"
echo ""
echo "  Next: Quit Claude Desktop and reopen it."
echo "  JARVIS will appear under 🔨 Tools."
echo ""
echo "  ACCOUNTS folder: $ACCOUNTS_DIR"
echo ""
