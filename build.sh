#!/bin/bash
# Build script for Auto-Accept
# Run this to create the executable for Mac/Linux

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║       Auto-Accept Build Script (Mac/Linux)                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install uv from https://docs.astral.sh/uv/getting-started/"
    exit 1
fi

echo "✓ uv found"
echo ""

# Sync dependencies from pyproject.toml
echo "📦 Installing dependencies..."
uv sync

echo ""
echo "📦 Installing PyInstaller..."
uv pip install pyinstaller

echo ""
echo "🔨 Building executable..."
echo ""

# Build with PyInstaller using uv
uv run pyinstaller --onefile --console \
    --name auto-accept \
    --hidden-import=selenium \
    --hidden-import=rich \
    --hidden-import=src \
    --hidden-import=src.core \
    --hidden-import=src.core.browser \
    --hidden-import=src.core.gmail \
    --hidden-import=src.core.scanner \
    --hidden-import=src.config \
    --hidden-import=src.config.constants \
    --hidden-import=src.utils \
    --hidden-import=src.utils.config_init \
    --hidden-import=src.utils.tracker \
    --hidden-import=src.utils.ui \
    main.py

echo ""
echo "✓ Build complete!"
echo ""
echo "📍 Executable location:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "   dist/auto-accept"
    echo ""
    echo "📝 To make it executable:"
    echo "   chmod +x dist/auto-accept"
    echo ""
    echo "▶️  To run it:"
    echo "   ./dist/auto-accept"
else
    echo "   dist/auto-accept"
    echo ""
    echo "▶️  To run it:"
    echo "   ./dist/auto-accept"
fi

echo ""
echo "✅ Done! Your executable is ready to distribute."
