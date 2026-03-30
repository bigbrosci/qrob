#!/bin/bash
# Build script for creating executables locally
# Usage: ./build.sh [windows|macos|linux|all]

set -e

cd "$(dirname "$0")"

echo "🔨 Building INCAR Generator Executable..."
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt
pip install -q pyinstaller

# Build based on argument
BUILD_TYPE=${1:-all}

if [ "$BUILD_TYPE" = "linux" ] || [ "$BUILD_TYPE" = "all" ]; then
    echo "🐧 Building Linux executable..."
    pyinstaller build_spec.spec --distpath dist/linux --workpath build/linux
    echo "✅ Linux executable created: dist/linux/INCAR_Generator"
    echo ""
fi

if [ "$BUILD_TYPE" = "macos" ] || [ "$BUILD_TYPE" = "all" ]; then
    echo "🍎 Building macOS executable..."
    pyinstaller build_spec.spec --distpath dist/macos --workpath build/macos
    echo "✅ macOS app created: dist/macos/INCAR_Generator.app"
    echo ""
fi

if [ "$BUILD_TYPE" = "windows" ] || [ "$BUILD_TYPE" = "all" ]; then
    echo "🪟 Building Windows executable..."
    pyinstaller build_spec.spec --distpath dist/windows --workpath build/windows
    echo "✅ Windows executable created: dist/windows/INCAR_Generator.exe"
    echo ""
fi

echo "✨ Build complete!"
echo ""
echo "Output locations:"
echo "  Linux:   dist/linux/INCAR_Generator"
echo "  macOS:   dist/macos/INCAR_Generator.app"
echo "  Windows: dist/windows/INCAR_Generator.exe"
