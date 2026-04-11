#!/bin/bash
# JARVIS MCP — Setup Wrapper (for backwards compatibility)
# This script delegates to the universal Python installer.
# For direct setup, run: python3 install.py

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║          JARVIS MCP — Universal Setup             ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# Find Python 3
PYTHON=""
for candidate in python3 python; do
    if command -v "$candidate" &>/dev/null; then
        VERSION=$("$candidate" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0")
        echo "Found Python: $candidate ($VERSION)"
        PYTHON="$candidate"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo ""
    echo "❌ Python not found!"
    echo ""
    echo "Please install Python 3.9 or later from:"
    echo "  https://www.python.org/downloads/"
    echo ""
    exit 1
fi

echo ""
echo "Running universal installer..."
echo ""

# Run the Python installer
"$PYTHON" install.py

exit $?
