#!/bin/bash
# JARVIS v3 Universal Installation - Works on any platform
# Complete autonomous setup with zero manual configuration

set -e

echo "🚀 JARVIS v3 Universal Installation"
echo "===================================="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check Python
echo "📋 Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo "  ✓ Python $PYTHON_VERSION"
else
    echo "❌ Python 3 not found. Install Python 3.11+ first."
    exit 1
fi

# Check if bootstrap needs to run
if [ ! -f "scripts/setup_jarvis_universal.py" ]; then
    echo "📦 Installing bootstrap components..."
    pip install -q -r requirements-universal.txt
fi

# Run universal bootstrap
echo "🔧 Running universal bootstrap..."
python3 scripts/setup_jarvis_universal.py

# Make start script executable
chmod +x start_jarvis.sh 2>/dev/null || true

echo ""
echo "✅ JARVIS v3 Universal Installation Complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your NVIDIA_API_KEY"
echo "  2. Run: ./start_jarvis.sh"
echo ""
echo "🎯 JARVIS is ready for autonomous operation!"