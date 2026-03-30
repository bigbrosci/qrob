#!/usr/bin/env bash
# Q-robot INCAR Generator - Quick Setup Script

echo "=========================================="
echo "Q-robot INCAR Generator - Setup"
echo "=========================================="
echo ""

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "📁 Setting up in: $SCRIPT_DIR"
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$SCRIPT_DIR/venv"
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source "$SCRIPT_DIR/venv/bin/activate"

# Install requirements
echo "📥 Installing requirements..."
pip install -q -r "$SCRIPT_DIR/requirements.txt"
echo "✓ Requirements installed"

echo ""
echo "=========================================="
echo "✓ Setup complete!"
echo "=========================================="
echo ""
echo "To start the server, run:"
echo "  cd $SCRIPT_DIR"
echo "  source venv/bin/activate"
echo "  python3 app.py"
echo ""
echo "Then open your browser to: http://localhost:5000"
echo ""
