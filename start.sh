#!/bin/bash
# Start MSR Event Hub: Build frontend and launch server
# Compatible with Linux/macOS

set -e

echo "======================================"
echo "MSR Event Hub Startup"
echo "======================================"
echo ""
# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python -m venv .venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Check if dependencies are installed
if ! .venv/bin/pip list 2>/dev/null | grep -q "fastapi"; then
    echo "Installing Python dependencies..."
    .venv/bin/pip install fastapi uvicorn[standard] azure-identity python-dotenv pydantic pydantic-settings agent-framework-azure-ai
    echo "✓ Python dependencies installed"
fi
echo ""
# Check if frontend needs building
FRONTEND_DIST="web/chat/dist"
FRONTEND_PKG="web/chat/package.json"

if [ -f "$FRONTEND_PKG" ]; then
    if [ ! -d "$FRONTEND_DIST" ]; then
        echo "Frontend not built. Building..."
        
        cd web/chat
        
        # Install dependencies if node_modules missing
        if [ ! -d "node_modules" ]; then
            echo "Installing frontend dependencies..."
            npm install
        fi
        
        # Build frontend
        echo "Building frontend..."
        npm run build
        
        cd ../..
        echo "✓ Frontend built successfully"
    else
        echo "✓ Frontend already built"
    fi
else
    echo "⚠ Frontend package.json not found, skipping build"
fi

echo ""
echo "Starting MSR Event Hub server..."
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠ No .env file found. Copy .env.example to .env and configure:"
    echo "   cp .env.example .env"
    echo ""
fi

# Start Python server (using venv Python)
.venv/bin/python main.py
