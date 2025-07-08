#!/bin/bash

# TrendScope Backend Development Startup Script
# This script starts the backend server in development mode

echo "🚀 Starting TrendScope Backend in Development Mode..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if we're in the backend directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Please run this script from the backend directory"
    exit 1
fi

# Install dependencies if needed
if [ ! -d ".venv" ]; then
    echo "📦 Installing dependencies..."
    uv sync
fi

# Set environment variables
export PYTHONPATH=$(pwd)/src
export HOST=127.0.0.1
export PORT=8000

echo "🔧 Configuration:"
echo "   - Host: $HOST"
echo "   - Port: $PORT"
echo "   - Python Path: $PYTHONPATH"
echo ""

echo "📝 Access URLs:"
echo "   - API: http://localhost:8000"
echo "   - Health Check: http://localhost:8000/health"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - ReDoc: http://localhost:8000/redoc"
echo ""

echo "🌟 Starting server..."
echo "   Press Ctrl+C to stop the server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Start the server
uv run uvicorn trendscope_backend.api.main:app --host $HOST --port $PORT --reload