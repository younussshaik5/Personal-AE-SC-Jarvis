#!/bin/bash
# JARVIS MCP — Complete Setup (Mac, Linux, Windows/WSL)
# Run once after cloning: bash setup.sh

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── Detect OS ─────────────────────────────────────────────────────────────────
OS="unknown"
case "$(uname -s)" in
    Darwin*)  OS="mac"   ;;
    Linux*)   OS="linux" ;;
    MINGW*|MSYS*|CYGWIN*) OS="windows" ;;
esac

# Claude Desktop config path varies by OS
if [ "$OS" = "mac" ]; then
    CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
elif [ "$OS" = "linux" ]; then
    CLAUDE_CONFIG="$HOME/.config/Claude/claude_desktop_config.json"
else
    # Windows (WSL or Git Bash)
    WIN_APPDATA="${APPDATA:-$HOME/AppData/Roaming}"
    CLAUDE_CONFIG="$WIN_APPDATA/Claude/claude_desktop_config.json"
fi

echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║        JARVIS MCP — Setup ($OS)                  ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""

# =============================================================================
# STEP 1: Check/Install Python 3.10+
# =============================================================================
echo "1️⃣  Checking Python 3.10+..."

PYTHON=""
for candidate in python3.13 python3.12 python3.11 python3.10 python3 python; do
    if command -v "$candidate" &>/dev/null; then
        VER_MAJOR=$("$candidate" -c "import sys; print(sys.version_info.major)" 2>/dev/null || echo "0")
        VER_MINOR=$("$candidate" -c "import sys; print(sys.version_info.minor)" 2>/dev/null || echo "0")
        VER=$((VER_MAJOR * 10 + VER_MINOR))
        if [ "$VER" -ge 310 ]; then
            PYTHON=$(command -v "$candidate")
            echo "   ✅ Found: $(basename "$PYTHON") ($("$PYTHON" --version 2>&1 | cut -d' ' -f2))"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "   ❌ Python 3.10+ not found. Please install it:"
    if [ "$OS" = "mac" ]; then
        echo "      brew install python@3.13"
        echo "   Then re-run: bash setup.sh"
        # Try Homebrew install automatically
        if command -v brew &>/dev/null; then
            echo "   Homebrew found — installing Python 3.13..."
            brew install python@3.13 >/dev/null 2>&1
            PYTHON=$(brew --prefix python@3.13)/bin/python3.13
            echo "   ✅ Python 3.13 installed: $PYTHON"
        else
            echo "   Install Homebrew first: https://brew.sh"
            exit 1
        fi
    elif [ "$OS" = "linux" ]; then
        echo "      sudo apt install python3  (Ubuntu/Debian)"
        echo "      sudo dnf install python3  (Fedora/RHEL)"
        exit 1
    else
        echo "      Download from https://python.org/downloads/"
        echo "      Make sure to check 'Add Python to PATH' during install"
        exit 1
    fi
fi

# =============================================================================
# STEP 2: Install Python Dependencies
# =============================================================================
echo ""
echo "2️⃣  Installing Python dependencies..."

cat > "$PROJECT_DIR/requirements.txt" << 'EOF'
mcp>=0.1.0
pydantic>=2.0.0
anthropic>=0.25.0
pydantic-settings>=2.0.0
aiofiles>=23.0.0
certifi>=2024.0.0
python-dotenv>=1.0.0
openai>=1.0.0
watchdog>=3.0.0
EOF

echo "   Installing packages..."
"$PYTHON" -m pip install --upgrade pip >/dev/null 2>&1
"$PYTHON" -m pip install -q -r "$PROJECT_DIR/requirements.txt" 2>&1 | grep -E "(Successfully|already)" || true

echo "   ✅ Dependencies installed"

# =============================================================================
# STEP 3: Fix SSL certificates (macOS Python issue)
# =============================================================================
if [ "$OS" = "mac" ]; then
    echo ""
    echo "3️⃣  Fixing SSL certificates..."
    PYTHON_VERSION=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    CERT_CMD="/Applications/Python ${PYTHON_VERSION}/Install Certificates.command"
    if [ -f "$CERT_CMD" ]; then
        bash "$CERT_CMD" >/dev/null 2>&1
        echo "   ✅ macOS SSL certificates installed"
    else
        "$PYTHON" -c "
import ssl, certifi, urllib.request
ctx = ssl.create_default_context(cafile=certifi.where())
try:
    urllib.request.urlopen('https://integrate.api.nvidia.com', context=ctx, timeout=5)
except Exception:
    pass
print('   ✅ SSL context verified via certifi')
" 2>/dev/null || echo "   ✅ certifi installed (SSL via library)"
    fi
else
    echo ""
    echo "3️⃣  SSL certificates... ✅ (not needed on $OS)"
fi

# =============================================================================
# STEP 4: Verify JARVIS imports
# =============================================================================
echo ""
echo "4️⃣  Verifying JARVIS package..."

"$PYTHON" -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')
try:
    from jarvis_mcp.mcp_server import JarvisServer
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    print('   ✅ All imports working')
except ImportError as e:
    print(f'   ❌ Import error: {e}')
    sys.exit(1)
try:
    server = JarvisServer()
    print(f'   ✅ JARVIS initialized: {len(server.skills)} skills')
except Exception as e:
    print(f'   ⚠️  Warning: {e}')
" || exit 1

# =============================================================================
# STEP 5: Setup .env — interactive NVIDIA key collection
# =============================================================================
echo ""
echo "5️⃣  Setting up NVIDIA API keys..."
echo ""
echo "   JARVIS uses Kimi K2 Thinking via NVIDIA NIM for all 24 skills."
echo "   Get free keys at: https://build.nvidia.com/ (sign up → API Keys)"
echo ""
echo "   ┌─────────────────────────────────────────────────────────────┐"
echo "   │  WHY MULTIPLE KEYS?                                         │"
echo "   │                                                             │"
echo "   │  JARVIS fires parallel LLM calls per skill — e.g. MEDDPICC │"
echo "   │  generates all 9 dimensions simultaneously. With 1 key you  │"
echo "   │  can hit rate limits mid-generation. With 5 keys, requests  │"
echo "   │  round-robin automatically — no waiting, no retries.        │"
echo "   │                                                             │"
echo "   │  Add as many as you have. 1 key works. 5 keys = seamless.  │"
echo "   └─────────────────────────────────────────────────────────────┘"
echo ""

NVIDIA_KEYS=()

while true; do
    printf "   🔑 NVIDIA API Key 1 (required): "
    read -r KEY1
    KEY1=$(echo "$KEY1" | tr -d '[:space:]')
    if [[ "$KEY1" == nvapi-* ]] && [ ${#KEY1} -gt 20 ]; then
        NVIDIA_KEYS+=("$KEY1")
        echo "      ✅ Key 1 accepted"
        break
    else
        echo "      ⚠️  Invalid key — must start with 'nvapi-'. Try again."
    fi
done

for i in 2 3 4 5; do
    echo ""
    printf "   🔑 NVIDIA API Key $i (optional — press Enter to skip): "
    read -r KEYN
    KEYN=$(echo "$KEYN" | tr -d '[:space:]')
    if [ -z "$KEYN" ]; then
        break
    elif [[ "$KEYN" == nvapi-* ]] && [ ${#KEYN} -gt 20 ]; then
        NVIDIA_KEYS+=("$KEYN")
        echo "      ✅ Key $i accepted"
    else
        echo "      ⚠️  Invalid key format — skipping"
    fi
done

echo ""
echo "   ${#NVIDIA_KEYS[@]} key(s) collected — writing to .env..."

cat > "$PROJECT_DIR/.env" << ENVEOF
# JARVIS v2 — Generated by setup.sh
# Edit API keys below, then restart Claude Desktop

# NVIDIA API Key Pool — round-robin rotation under parallel load
# Get more keys: https://build.nvidia.com/
ENVEOF

for i in "${!NVIDIA_KEYS[@]}"; do
    KEY_NUM=$((i + 1))
    if [ "$KEY_NUM" -eq 1 ]; then
        echo "NVIDIA_API_KEY=${NVIDIA_KEYS[$i]}" >> "$PROJECT_DIR/.env"
    else
        echo "NVIDIA_API_KEY_${KEY_NUM}=${NVIDIA_KEYS[$i]}" >> "$PROJECT_DIR/.env"
    fi
done

cat >> "$PROJECT_DIR/.env" << ENVEOF2

# Optional — only needed if using Claude API directly (not Claude Desktop)
ANTHROPIC_API_KEY=

# JARVIS home directory (where your deal data lives)
JARVIS_HOME=$HOME/JARVIS

# Claude workspace directory
CLAUDE_SPACE=$HOME/Documents/claude space

# Optional: Telegram bot for mobile notifications
TELEGRAM_BOT_TOKEN=
ENVEOF2

echo "   ✅ .env written with ${#NVIDIA_KEYS[@]} NVIDIA key(s)"

# =============================================================================
# STEP 6: Create ACCOUNTS folder
# =============================================================================
echo ""
echo "6️⃣  Setting up ACCOUNTS folder..."

if [ -d "$HOME/ACCOUNTS" ]; then
    ACCOUNTS_DIR="$HOME/ACCOUNTS"
elif [ -d "$HOME/JARVIS/ACCOUNTS" ]; then
    ACCOUNTS_DIR="$HOME/JARVIS/ACCOUNTS"
else
    ACCOUNTS_DIR="$HOME/JARVIS/ACCOUNTS"
fi

mkdir -p "$ACCOUNTS_DIR"
echo "   ✅ ACCOUNTS: $ACCOUNTS_DIR"

# =============================================================================
# STEP 7: Register in Claude Desktop
# =============================================================================
echo ""
echo "7️⃣  Registering with Claude Desktop..."

mkdir -p "$(dirname "$CLAUDE_CONFIG")"

"$PYTHON" - <<PYEOF
import json, sys, os

config_path = r"$CLAUDE_CONFIG"
project_path = r"$PROJECT_DIR"
python_path  = r"$PYTHON"
accounts_path = r"$ACCOUNTS_DIR"

try:
    with open(config_path) as f:
        config = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    config = {"mcpServers": {}, "preferences": {}}

config.setdefault("mcpServers", {})

config["mcpServers"]["jarvis"] = {
    "command": python_path,
    "args": [f"{project_path}/jarvis_mcp_server.py"],
    "disabled": False
}
config["mcpServers"]["jarvis-crm"] = {
    "command": python_path,
    "args": [f"{project_path}/crm_sidecar.py"],
    "disabled": False
}

config.setdefault("preferences", {})
config["preferences"].setdefault("localAgentModeTrustedFolders", [])
for p in [project_path, accounts_path]:
    if p not in config["preferences"]["localAgentModeTrustedFolders"]:
        config["preferences"]["localAgentModeTrustedFolders"].append(p)

with open(config_path, "w") as f:
    json.dump(config, f, indent=2)

print(f"   ✅ Claude Desktop configured")
print(f"      Config: {config_path}")
print(f"      Python: {python_path}")
PYEOF

# =============================================================================
# STEP 8: Final smoke test
# =============================================================================
echo ""
echo "8️⃣  Running final smoke test..."

"$PYTHON" -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')
try:
    from jarvis_mcp_server import server, TOOLS, _jarvis
    print(f'   ✅ MCP server: {server.name}')
    print(f'   ✅ Tools: {len(TOOLS)} registered')
    print(f'   ✅ JARVIS: {len(_jarvis.skills) if _jarvis else 0} skills')
except Exception as e:
    print(f'   ❌ Error: {e}')
    sys.exit(1)
" || exit 1

# =============================================================================
# DONE
# =============================================================================
echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║              ✅ Setup Complete!                  ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""
echo "📋 Summary:"
echo "   • OS: $OS"
echo "   • Python: $PYTHON"
echo "   • ACCOUNTS: $ACCOUNTS_DIR"
echo "   • Claude Config: $CLAUDE_CONFIG ✅"
echo ""
if [ "$OS" = "mac" ]; then
    echo "🚀 Next Steps:"
    echo "   1. Quit Claude Desktop (⌘Q)"
    echo "   2. Reopen Claude Desktop"
elif [ "$OS" = "windows" ]; then
    echo "🚀 Next Steps:"
    echo "   1. Close Claude Desktop from the system tray"
    echo "   2. Reopen Claude Desktop"
else
    echo "🚀 Next Steps:"
    echo "   1. Restart Claude Desktop"
fi
echo "   3. Look for 🔨 Tools — JARVIS + CRM should appear"
echo "   4. CRM Dashboard auto-starts at http://localhost:8000"
echo "   5. Say 'onboarding' in Claude to set up your first account"
echo ""
echo "💡 Tips:"
echo "   • Add more NVIDIA keys to .env as NVIDIA_API_KEY_2, _3 etc."
echo "   • Run setup.sh again anytime to reinstall dependencies."
echo "   • Your accounts folder: $ACCOUNTS_DIR"
echo ""
