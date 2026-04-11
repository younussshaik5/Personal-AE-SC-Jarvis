#!/bin/bash
set -e

echo "🚀 JARVIS MCP - Automatic Setup"
echo ""
echo "This script will:"
echo "  1. Create virtual environment"
echo "  2. Install dependencies"
echo "  3. Setup account folders"
echo "  4. Create .env from .env.example"
echo "  5. Ready to use"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.9+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Python $PYTHON_VERSION found"
echo ""

# Create venv
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate venv (Unix/Mac/Git Bash - different from Windows CMD)
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    PYTHON_BIN="python"
    PIP_BIN="pip"
elif [ -f "venv/Scripts/activate" ]; then
    # This path exists but bash on Windows requires source, not . activate
    echo "⚠️  Using venv from Windows path - ensure you're in Git Bash or WSL, not CMD"
    source venv/Scripts/activate.bat 2>/dev/null || source venv/Scripts/activate
    PYTHON_BIN="python"
    PIP_BIN="pip"
else
    echo "❌ Failed to find venv activation script"
    exit 1
fi

echo "✓ Virtual environment created"
echo ""

# Install dependencies
echo "📚 Installing dependencies..."
$PYTHON_BIN -m pip install --upgrade pip --quiet
$PYTHON_BIN -m pip install --quiet -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Create .env if not exists
if [ ! -f .env ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    echo "✓ .env created"
    echo ""
    echo "⚠️  REQUIRED: Edit .env and add your NVIDIA_API_KEY"
    echo "   nano .env"
    echo ""
else
    echo "✓ .env already exists"
    echo ""
fi

# Create account folders
echo "📁 Setting up account folders..."
# Use JARVIS_HOME if set, otherwise create in user home
JARVIS_HOME="${JARVIS_HOME:-$HOME/JARVIS}"
ACCOUNTS_DIR="$JARVIS_HOME/ACCOUNTS"
mkdir -p "$ACCOUNTS_DIR"
echo "✓ Accounts directory: $ACCOUNTS_DIR"
echo ""

# Create MEMORY folder
MEMORY_DIR="$JARVIS_HOME/MEMORY"
mkdir -p "$MEMORY_DIR"
echo "✓ Memory directory: $MEMORY_DIR"
echo ""

# Copy example accounts if ACCOUNTS is empty
if [ ! -d "$ACCOUNTS_DIR/AcmeCorp" ]; then
    echo "📋 Copying example accounts..."
    cp -r examples/accounts/* "$ACCOUNTS_DIR/" 2>/dev/null || true
    echo "✓ Example accounts copied (AcmeCorp, TechStartup, GlobalBank)"
    echo ""
fi

# Run tests
echo "✅ Running tests..."
pytest -q tests/ 2>/dev/null || pytest tests/ 2>&1 | head -20
echo ""

echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add NVIDIA_API_KEY"
echo "  2. Run tests: make test"
echo "  3. Use with Claude Code:"
echo "     - Add MCP server to Claude Code settings"
echo "     - Command: python -m jarvis_mcp.mcp_server"
echo ""
echo "Try it:"
echo "  source venv/bin/activate  # Activate venv"
echo "  python -m jarvis_mcp.mcp_server  # Start server"
echo ""
