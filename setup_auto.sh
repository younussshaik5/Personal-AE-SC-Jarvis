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
source venv/bin/activate || . venv/Scripts/activate
echo "✓ Virtual environment created"
echo ""

# Install dependencies
echo "📚 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -e ".[dev]"
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
ACCOUNTS_DIR="${HOME}/Documents/claude space/ACCOUNTS"
mkdir -p "$ACCOUNTS_DIR"
echo "✓ Accounts directory: $ACCOUNTS_DIR"
echo ""

# Create MEMORY folder
MEMORY_DIR="${HOME}/Documents/claude space/MEMORY"
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
