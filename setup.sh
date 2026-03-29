#!/bin/bash
set -e

# ============================================
#   JARVIS v2 — Portable One-Command Setup
#   Works on macOS, Linux, and WSL
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors (safe for terminals without color support)
if [ -t 1 ]; then
  GREEN='\033[0;32m'
  BLUE='\033[0;34m'
  YELLOW='\033[1;33m'
  RED='\033[0;31m'
  BOLD='\033[1m'
  NC='\033[0m'
else
  GREEN='' BLUE='' YELLOW='' RED='' BOLD='' NC=''
fi

info()  { echo -e "${BLUE}$*${NC}"; }
ok()    { echo -e "${GREEN}$*${NC}"; }
warn()  { echo -e "${YELLOW}$*${NC}"; }
err()   { echo -e "${RED}$*${NC}"; }

echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}   J.A.R.V.I.S. v2 — Portable Setup${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo ""

# ── Step 1: Detect OS ─────────────────────────────────────

info "[1/8] Detecting system..."
OS="$(uname -s)"
ARCH="$(uname -m)"
case "$OS" in
  Darwin*)  PLATFORM="macos" ;;
  Linux*)
    if grep -qi microsoft /proc/version 2>/dev/null; then
      PLATFORM="wsl"
    else
      PLATFORM="linux"
    fi
    ;;
  *)        PLATFORM="unknown" ;;
esac
echo "  Platform: $PLATFORM ($ARCH)"

# Determine package manager
PKG_MGR=""
NEED_BREW=0
if [ "$PLATFORM" = "macos" ]; then
  if command -v brew >/dev/null 2>&1; then
    PKG_MGR="brew"
  else
    warn "  Homebrew not found — will install it first"
    PKG_MGR="brew"
    NEED_BREW=1
  fi
elif [ "$PLATFORM" = "linux" ] || [ "$PLATFORM" = "wsl" ]; then
  if command -v apt-get >/dev/null 2>&1; then
    PKG_MGR="apt"
  elif command -v dnf >/dev/null 2>&1; then
    PKG_MGR="dnf"
  elif command -v yum >/dev/null 2>&1; then
    PKG_MGR="yum"
  elif command -v pacman >/dev/null 2>&1; then
    PKG_MGR="pacman"
  else
    err "  ERROR: No supported package manager found (apt/dnf/yum/pacman)"
    err "  Install Python 3.11+, Node.js 18+, and ffmpeg manually, then re-run."
    exit 1
  fi
  echo "  Package manager: $PKG_MGR"
fi

# ── Step 2: Check & Install Dependencies ─────────────────

info "[2/8] Checking dependencies..."
MISSING=()

# -- Homebrew (macOS only) --
if [ "$NEED_BREW" = "1" ]; then
  info "  Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" </dev/null
  # Add to PATH for this session
  if [ -x /opt/homebrew/bin/brew ]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [ -x /usr/local/bin/brew ]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi
  ok "  ✓ Homebrew installed"
fi

install_pkg() {
  local name="$1"
  case "$PKG_MGR" in
    brew)   brew install "$name" ;;
    apt)    sudo apt-get update -qq && sudo apt-get install -y -qq "$name" ;;
    dnf)    sudo dnf install -y -q "$name" ;;
    yum)    sudo yum install -y -q "$name" ;;
    pacman) sudo pacman -S --noconfirm "$name" ;;
  esac
}

# -- Python 3 --
if command -v python3 >/dev/null 2>&1; then
  PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
  if [ "$PY_MINOR" -ge 11 ] 2>/dev/null; then
    ok "  ✓ Python $(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  else
    warn "  Python too old (need ≥ 3.11) — will upgrade"
    MISSING+=("python3")
  fi
else
  warn "  Python 3 not found — will install"
  MISSING+=("python3")
fi

# -- pip --
if ! python3 -m pip --version >/dev/null 2>&1; then
  warn "  pip not found — will install"
  MISSING+=("pip")
fi

# -- Node.js --
if command -v node >/dev/null 2>&1; then
  NODE_MAJOR=$(node -v | sed 's/v//' | cut -d. -f1)
  if [ "$NODE_MAJOR" -ge 18 ] 2>/dev/null; then
    ok "  ✓ Node.js $(node -v)"
  else
    warn "  Node.js too old (need ≥ 18) — will upgrade"
    MISSING+=("node")
  fi
else
  warn "  Node.js not found — will install"
  MISSING+=("node")
fi

# -- npm --
if command -v npm >/dev/null 2>&1; then
  ok "  ✓ npm $(npm -v)"
else
  warn "  npm not found — will install"
  MISSING+=("npm")
fi

# -- ffmpeg (optional but recommended) --
if command -v ffmpeg >/dev/null 2>&1; then
  ok "  ✓ ffmpeg (meeting recording support)"
else
  warn "  ffmpeg not found (optional — needed for meeting recordings)"
  MISSING+=("ffmpeg")
fi

# -- C++ build tools (needed for better-sqlite3 native addon) --
HAS_BUILD_TOOLS=false
if [ "$PLATFORM" = "macos" ]; then
  if xcode-select -p >/dev/null 2>&1; then
    HAS_BUILD_TOOLS=true
    ok "  ✓ Xcode CLI tools (native addon support)"
  else
    warn "  Xcode CLI tools not found — needed for better-sqlite3"
  fi
elif command -v g++ >/dev/null 2>&1 || command -v c++ >/dev/null 2>&1; then
  HAS_BUILD_TOOLS=true
  ok "  ✓ C++ compiler (native addon support)"
else
  warn "  C++ compiler not found — needed for better-sqlite3"
fi

if [ "$HAS_BUILD_TOOLS" = "false" ]; then
  if [ "$PLATFORM" = "macos" ]; then
    info "  Installing Xcode CLI tools..."
    xcode-select --install 2>/dev/null || true
    # Wait for user to accept the prompt
    until xcode-select -p >/dev/null 2>&1; do sleep 5; done
    ok "  ✓ Xcode CLI tools installed"
  elif [ "$PLATFORM" = "linux" ] || [ "$PLATFORM" = "wsl" ]; then
    info "  Installing build-essential..."
    case "$PKG_MGR" in
      apt)    sudo apt-get install -y -qq build-essential ;;
      dnf)    sudo dnf groupinstall -y -q "Development Tools" ;;
      yum)    sudo yum groupinstall -y -q "Development Tools" ;;
      pacman) sudo pacman -S --noconfirm base-devel ;;
    esac
    ok "  ✓ Build tools installed"
  fi
fi

# -- Install missing packages --
if [ ${#MISSING[@]} -gt 0 ]; then
  echo ""
  info "  Installing missing packages: ${MISSING[*]}"

  for pkg in "${MISSING[@]}"; do
    case "$pkg" in
      python3)
        if [ "$PKG_MGR" = "brew" ]; then
          install_pkg python@3.12 2>/dev/null || install_pkg python3
        else
          install_pkg python3
        fi
        ok "  ✓ Python installed"
        ;;
      pip)
        if [ "$PLATFORM" = "macos" ]; then
          python3 -m ensurepip --upgrade 2>/dev/null || true
        else
          install_pkg python3-pip
        fi
        ok "  ✓ pip installed"
        ;;
      node)
        if [ "$PKG_MGR" = "brew" ]; then
          install_pkg node
        elif [ "$PKG_MGR" = "apt" ]; then
          curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - >/dev/null 2>&1
          sudo apt-get install -y -qq nodejs
        else
          install_pkg nodejs
        fi
        ok "  ✓ Node.js installed"
        ;;
      npm)
        if [ "$PKG_MGR" = "apt" ]; then
          install_pkg npm
        elif ! command -v npm >/dev/null 2>&1; then
          curl -qL https://www.npmjs.com/install.sh | sh >/dev/null 2>&1
        fi
        ok "  ✓ npm installed"
        ;;
      ffmpeg)
        install_pkg ffmpeg 2>/dev/null || warn "  Could not install ffmpeg (optional, skipping)"
        ;;
    esac
  done
  echo ""
fi

# Verify critical tools
command -v python3 >/dev/null 2>&1 || { err "ERROR: python3 not found after install attempt"; exit 1; }
command -v node >/dev/null 2>&1 || { err "ERROR: node not found after install attempt"; exit 1; }
command -v npm >/dev/null 2>&1 || { err "ERROR: npm not found after install attempt"; exit 1; }

# ── Step 3: Install Python Dependencies ──────────────────

info "[3/8] Installing Python dependencies..."
python3 -m pip install -r requirements-jarvis.txt --quiet 2>&1 | tail -1
ok "  ✓ Python packages installed"

# ── Step 4: Build MCP Servers ────────────────────────────

info "[4/8] Building MCP servers..."

# MCP Observer
if [ -d "mcp-opencode-observer" ]; then
  info "  Building MCP Observer..."
  (
    cd mcp-opencode-observer
    npm install --silent 2>&1 | tail -1
    npm run build 2>&1 | tail -1
  )
  ok "  ✓ MCP Observer built"
else
  warn "  mcp-opencode-observer/ not found, skipping"
fi

# JARVIS MCP Server
if [ -d "mcp-jarvis-server" ]; then
  info "  Building JARVIS MCP Server..."
  (
    cd mcp-jarvis-server
    npm install --silent 2>&1 | tail -1
    npm run build 2>&1 | tail -1
  )
  ok "  ✓ JARVIS MCP Server built"
else
  warn "  mcp-jarvis-server/ not found, skipping"
fi

# ── Step 5: Detect OpenCode ──────────────────────────────

info "[5/8] Detecting OpenCode..."
OPENCODE_DB_DEFAULT="$HOME/.local/share/opencode/opencode.db"
OPENCODE_DB_MACOS="$HOME/Library/Application Support/Accomplish/opencode/opencode.db"

OPENCODE_DB=""
if [ -f "$OPENCODE_DB_DEFAULT" ]; then
  OPENCODE_DB="$OPENCODE_DB_DEFAULT"
elif [ -f "$OPENCODE_DB_MACOS" ]; then
  OPENCODE_DB="$OPENCODE_DB_MACOS"
fi

if [ -n "$OPENCODE_DB" ]; then
  ok "  ✓ OpenCode detected: $OPENCODE_DB"
else
  warn "  OpenCode not found — conversation observer will start when OpenCode is installed"
fi

# ── Step 6: Interactive Prompts ──────────────────────────

info "[6/8] Configuration..."
echo ""

# JARVIS_HOME
JARVIS_HOME="${JARVIS_HOME:-$HOME/JARVIS}"
if [ -t 0 ]; then
  printf "  JARVIS data directory [$JARVIS_HOME]: "
  read -r JARVIS_HOME_INPUT
  JARVIS_HOME="${JARVIS_HOME_INPUT:-$JARVIS_HOME}"
fi
JARVIS_HOME="${JARVIS_HOME/#\~/$HOME}"
export JARVIS_HOME
echo ""

# CLAUDE_SPACE — auto-detect from current directory
CWD="$(pwd)"
if [ -t 0 ]; then
  printf "  Claude workspace folder [$CWD]: "
  read -r CLAUDE_SPACE_INPUT
  CLAUDE_SPACE="${CLAUDE_SPACE_INPUT:-$CWD}"
else
  CLAUDE_SPACE="$CWD"
fi
CLAUDE_SPACE="${CLAUDE_SPACE/#\~/$HOME}"
echo ""

# API Keys
if [ -t 0 ]; then
  printf "  NVIDIA API Key (required — get from https://build.nvidia.com/): "
  read -r NVIDIA_API_KEY
  if [ -z "$NVIDIA_API_KEY" ]; then
    warn "  ⚠ No NVIDIA key provided — you'll need to add it to .env later"
  fi
  echo ""

  printf "  Anthropic API Key (optional — press Enter to skip): "
  read -r ANTHROPIC_API_KEY
  echo ""
else
  NVIDIA_API_KEY=""
  ANTHROPIC_API_KEY=""
fi

# ── Step 7: Generate All Configs ─────────────────────────

info "[7/8] Generating config files..."
python3 scripts/generate_config.py \
  --jarvis-home "$JARVIS_HOME" \
  --claude-space "$CLAUDE_SPACE" \
  --nvidia-key "$NVIDIA_API_KEY" \
  --anthropic-key "$ANTHROPIC_API_KEY"

ok "  ✓ All configs generated"

# ── Step 8: Register with Claude Desktop & OpenCode ──────

info "[8/8] Registering with Claude Desktop..."
python3 scripts/register_mcp.py
ok "  ✓ MCP registered"

# ── Done ─────────────────────────────────────────────────

echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
ok "  ✅ JARVIS SETUP COMPLETE"
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "  Data directory: $JARVIS_HOME"
echo "  Claude workspace: $CLAUDE_SPACE"
echo ""
echo "  Start JARVIS:"
echo "    ./start_jarvis.sh"
echo ""
echo "  Claude Desktop commands:"
echo "    'list my accounts'"
echo "    'prep me for the Acme meeting'"
echo "    'show MEDDPICC for TechCorp'"
echo ""
echo "  Dashboard:"
echo "    http://localhost:8080"
echo ""
