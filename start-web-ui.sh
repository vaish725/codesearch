#!/bin/bash
# Quick start script for CodeSearch Web UI

echo "🚀 Starting CodeSearch Web UI..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

# Install if needed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing web dependencies..."
    pip3 install -e ".[web]"
fi

# Launch the web UI
python3 -m codesearch.web.server
