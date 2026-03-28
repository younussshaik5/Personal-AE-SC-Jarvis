#!/bin/bash
set -e

echo "============================================"
echo "  JARVIS v2 - Personal AE+SC Sales Assistant"
echo "  Setup Script"
echo "============================================"
echo ""

# Detect OS
OS=$(uname -s)
echo "[1/7] Detected OS: $OS"

# Check prerequisites
echo "[2/7] Checking prerequisites..."
command -v python3 >/dev/null 2>&1 || { echo "ERROR: Python 3.9+ required. Install from python.org"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "ERROR: Node.js 18+ required. Install from nodejs.org"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "ERROR: npm required. Comes with Node.js"; exit 1; }

PYTHON_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
NODE_VER=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
echo "  Python: $PYTHON_VER"
echo "  Node.js: v$NODE_VER"

# Check for ffmpeg (optional but recommended for meeting recording)
if command -v ffmpeg >/dev/null 2>&1; then
    echo "  ffmpeg: installed"
else
    echo "  ffmpeg: NOT installed (optional - needed for meeting recording)"
    echo "  Install with: brew install ffmpeg"
fi

# Install Python dependencies
echo ""
echo "[3/7] Installing Python dependencies..."
python3 -m pip install -r requirements-jarvis.txt --quiet 2>&1 | tail -1

# Install and build MCP Observer
echo ""
echo "[4/7] Building MCP Observer..."
if [ -d "mcp-opencode-observer" ]; then
    cd mcp-opencode-observer && npm install --silent 2>&1 | tail -1 && npm run build 2>&1 | tail -1 && cd ..
    echo "  MCP Observer built successfully"
else
    echo "  MCP Observer directory not found, skipping"
fi

# Install and build JARVIS MCP Server
echo ""
echo "[5/7] Building JARVIS MCP Server for Claude Desktop..."
cd mcp-jarvis-server && npm install --silent 2>&1 | tail -1 && npm run build 2>&1 | tail -1 && cd ..
echo "  JARVIS MCP Server built successfully"

# Create data directories
echo ""
echo "[6/7] Creating data directories..."
JARVIS_HOME="${JARVIS_HOME:-$HOME/Documents/claude space/JARVIS}"
mkdir -p "$JARVIS_HOME"/{ACCOUNTS,MEMORY,MEMORY/patterns,data/personas,data/templates,data/meeting_queue,logs,recordings}
echo "  JARVIS_HOME: $JARVIS_HOME"

# Setup .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "  Created .env from template"
    echo "  >>> IMPORTANT: Edit .env and add your NVIDIA_API_KEY <<<"
fi

# Register MCP server with Claude Desktop
echo ""
echo "[7/7] Registering JARVIS MCP server with Claude Desktop..."
python3 scripts/register_mcp.py
echo ""

echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your NVIDIA_API_KEY"
echo "  2. Run: ./start_jarvis.sh"
echo "  3. Open Claude Desktop - JARVIS MCP is ready"
echo ""
echo "Claude Desktop commands you can use:"
echo "  'list my accounts'"
echo "  'prep me for the TechCorp meeting'"
echo "  'process this meeting recording at /path/to/file.mp4'"
echo "  'show me MEDDPICC for TechCorp Corp'"
echo "  'create proposal for TechCorp Corp'"
echo ""
