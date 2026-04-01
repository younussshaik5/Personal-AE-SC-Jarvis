#!/bin/bash
# JARVIS MCP — Complete Zero-to-Hero Setup
# Run once after cloning: bash setup.sh
# Sets up Python, dependencies, Claude Desktop config, everything.

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║  JARVIS MCP — Complete Setup (Zero Dependencies)  ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""

# =============================================================================
# STEP 1: Check/Install Homebrew
# =============================================================================
echo "1️⃣  Checking Homebrew..."
if ! command -v brew &>/dev/null; then
    echo "   ℹ️  Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    echo "   ✅ Homebrew installed"
else
    echo "   ✅ Homebrew found"
fi

# =============================================================================
# STEP 2: Check/Install Python 3.13
# =============================================================================
echo ""
echo "2️⃣  Checking Python 3.10+..."

PYTHON=""
for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" &>/dev/null; then
        VER_MAJOR=$("$candidate" -c "import sys; print(sys.version_info.major)")
        VER_MINOR=$("$candidate" -c "import sys; print(sys.version_info.minor)")
        VER=$((VER_MAJOR * 10 + VER_MINOR))
        if [ "$VER" -ge 310 ]; then
            PYTHON=$(command -v "$candidate")
            echo "   ✅ Found: $(basename "$PYTHON") ($("$PYTHON" --version 2>&1 | cut -d' ' -f2))"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "   ℹ️  Installing Python 3.13 via Homebrew..."
    brew install python@3.13 >/dev/null 2>&1
    PYTHON=$(brew --prefix python@3.13)/bin/python3.13
    echo "   ✅ Python 3.13 installed: $PYTHON"
fi

# =============================================================================
# STEP 3: Install Python Dependencies
# =============================================================================
echo ""
echo "3️⃣  Installing Python dependencies..."

# Create a requirements.txt if it doesn't exist
if [ ! -f "$PROJECT_DIR/requirements.txt" ]; then
    cat > "$PROJECT_DIR/requirements.txt" << 'EOF'
mcp>=0.1.0
pydantic>=2.0.0
anthropic>=0.25.0
pydantic-settings>=2.0.0
aiofiles>=23.0.0
EOF
    echo "   📝 Created requirements.txt"
fi

echo "   Installing packages..."
"$PYTHON" -m pip install --upgrade pip >/dev/null 2>&1
"$PYTHON" -m pip install -q -r "$PROJECT_DIR/requirements.txt" 2>&1 | grep -E "(Successfully|already)" || true

echo "   ✅ Dependencies installed"

# =============================================================================
# STEP 4: Verify JARVIS imports
# =============================================================================
echo ""
echo "4️⃣  Verifying JARVIS package..."

"$PYTHON" -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')

# Test core imports
try:
    from jarvis_mcp.mcp_server import JarvisServer
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    print('   ✅ All imports working')
except ImportError as e:
    print(f'   ❌ Import error: {e}')
    sys.exit(1)

# Test JARVIS initialization
try:
    server = JarvisServer()
    print(f'   ✅ JARVIS initialized: {len(server.skills)} skills')
except Exception as e:
    print(f'   ⚠️  Warning: {e}')
" || exit 1

# =============================================================================
# STEP 5: Setup .env configuration
# =============================================================================
echo ""
echo "5️⃣  Setting up .env configuration..."

if [ ! -f "$PROJECT_DIR/.env" ]; then
    if [ -f "$PROJECT_DIR/.env.example" ]; then
        cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
        echo "   ✅ Created .env from .env.example"
        echo "   ℹ️  Edit .env and add your NVIDIA API key (or use existing key)"
        echo "      Location: $PROJECT_DIR/.env"
    else
        echo "   ⚠️  .env.example not found, skipping .env creation"
    fi
else
    echo "   ✅ .env already exists (skipping)"
fi

# =============================================================================
# STEP 6: Create ACCOUNTS folder
# =============================================================================
echo ""
echo "6️⃣  Setting up ACCOUNTS folder..."

# Check if user has custom ACCOUNTS location
if [ -d "$HOME/ACCOUNTS" ]; then
    ACCOUNTS_DIR="$HOME/ACCOUNTS"
elif [ -d "$HOME/JARVIS/ACCOUNTS" ]; then
    ACCOUNTS_DIR="$HOME/JARVIS/ACCOUNTS"
else
    ACCOUNTS_DIR="$HOME/Documents/claude space/ACCOUNTS"
fi

mkdir -p "$ACCOUNTS_DIR"
echo "   ✅ ACCOUNTS: $ACCOUNTS_DIR"

# =============================================================================
# STEP 7: Register in Claude Desktop
# =============================================================================
echo ""
echo "7️⃣  Registering with Claude Desktop..."

mkdir -p "$(dirname "$CLAUDE_CONFIG")"

# Use Python to safely update the JSON config
"$PYTHON" - <<PYEOF
import json
import sys

config_path = r"$CLAUDE_CONFIG"
project_path = r"$PROJECT_DIR"
python_path = r"$PYTHON"
accounts_path = r"$ACCOUNTS_DIR"

try:
    with open(config_path) as f:
        config = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    config = {"mcpServers": {}, "preferences": {}}

if "mcpServers" not in config:
    config["mcpServers"] = {}

# Register JARVIS MCP server
config["mcpServers"]["jarvis"] = {
    "command": python_path,
    "args": [f"{project_path}/jarvis_mcp_server.py"],
    "disabled": False
}

# Register JARVIS CRM sidecar (auto-starts CRM dashboard with Claude)
config["mcpServers"]["jarvis-crm"] = {
    "command": python_path,
    "args": [f"{project_path}/crm_sidecar.py"],
    "disabled": False
}

# Add trusted folder for Claude Code
if "preferences" not in config:
    config["preferences"] = {}

if "localAgentModeTrustedFolders" not in config["preferences"]:
    config["preferences"]["localAgentModeTrustedFolders"] = []

if project_path not in config["preferences"]["localAgentModeTrustedFolders"]:
    config["preferences"]["localAgentModeTrustedFolders"].append(project_path)

if accounts_path not in config["preferences"]["localAgentModeTrustedFolders"]:
    config["preferences"]["localAgentModeTrustedFolders"].append(accounts_path)

with open(config_path, "w") as f:
    json.dump(config, f, indent=2)

print(f"   ✅ Claude Desktop configured")
print(f"      Python: {python_path}")
print(f"      JARVIS: {project_path}/jarvis_mcp_server.py")
print(f"      CRM sidecar: {project_path}/crm_sidecar.py")
print(f"      Accounts: {accounts_path}")
PYEOF

# =============================================================================
# STEP 8: Final smoke test
# =============================================================================
echo ""
echo "8️⃣  Running final smoke test..."

"$PYTHON" << 'SMOKENTEST'
import sys
import asyncio
sys.path.insert(0, '$PROJECT_DIR')

try:
    from jarvis_mcp_server import server, TOOLS, _jarvis

    print(f"   ✅ MCP server: {server.name}")
    print(f"   ✅ Tools: {len(TOOLS)} registered")
    print(f"   ✅ JARVIS: {len(_jarvis.skills) if _jarvis else 0} skills")

    # List first 5 tools
    print(f"\n   Available tools:")
    for tool in TOOLS[:5]:
        print(f"      • {tool.name}")
    if len(TOOLS) > 5:
        print(f"      • ... and {len(TOOLS) - 5} more")

except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)
SMOKENTEST

# =============================================================================
# DONE
# =============================================================================
echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║              ✅ Setup Complete!                  ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""
echo "📋 Summary:"
echo "   • Python: $PYTHON"
echo "   • Dependencies: Installed ✅"
echo "   • Project: $PROJECT_DIR"
echo "   • ACCOUNTS: $ACCOUNTS_DIR"
echo "   • Claude Config: Updated ✅"
echo "   • JARVIS MCP: Registered ✅"
echo "   • CRM Sidecar: Registered ✅"
echo ""
echo "🚀 Next Steps:"
echo "   1. Add NVIDIA API key to .env file (if not done)"
echo "   2. Quit Claude Desktop (⌘Q)"
echo "   3. Reopen Claude Desktop"
echo "   4. Look for 🔨 Tools — JARVIS + CRM should appear"
echo "   5. CRM Dashboard auto-starts at http://localhost:8000"
echo ""
echo "💡 Tip: Run setup.sh again anytime to reinstall dependencies."
echo ""
