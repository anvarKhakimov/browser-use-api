#!/bin/bash

# Browser-Use API Startup Script
# Runs the API server on port 8765 with logs visible in console

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PORT=8765
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   Browser-Use API Service${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}✗ Virtual environment not found at $VENV_DIR${NC}"
    echo -e "${YELLOW}Run: uv venv --python 3.11 && source .venv/bin/activate && uv sync${NC}"
    exit 1
fi

# Check if port is in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${RED}✗ Port $PORT is already in use${NC}"
    echo -e "${YELLOW}Kill the process or choose a different port${NC}"
    echo -e "${YELLOW}To kill: lsof -ti:$PORT | xargs kill -9${NC}"
    exit 1
fi

# Check if .env exists
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${YELLOW}⚠ .env file not found, copying from .env.example${NC}"
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo -e "${YELLOW}⚠ Please edit .env and add your API keys${NC}"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Display configuration
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo -e "${GREEN}✓ Port: $PORT${NC}"
echo -e "${GREEN}✓ Project: $PROJECT_DIR${NC}"
echo ""

# Check for API keys
if ! grep -q "AIza" .env 2>/dev/null; then
    echo -e "${YELLOW}⚠ Warning: GOOGLE_API_KEY not configured in .env${NC}"
fi

echo -e "${BLUE}Starting server...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Start server (foreground, logs visible)
export PORT=$PORT
uvicorn app.main:app --host 0.0.0.0 --port $PORT --reload