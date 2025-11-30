#!/bin/bash

# Browser-Use API Installation Script
# This script sets up the development environment for the Browser-Use API

set -e  # Exit on error

echo "========================================="
echo "Browser-Use API Installation Script"
echo "========================================="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "uv installed successfully!"
    echo ""
else
    echo "uv is already installed."
    echo ""
fi

# Check Python version
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    echo "Found Python $python_version"
else
    echo "Error: Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
uv venv --python 3.11

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
uv sync

# Install development dependencies (optional)
read -p "Do you want to install development dependencies? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing development dependencies..."
    uv sync --extra dev
fi

# Check for .env file
echo ""
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "Creating .env file from .env.example..."
        cp .env.example .env
        echo ""
        echo "IMPORTANT: Please edit .env and add your API keys!"
        echo "  - Google API Key (recommended): https://aistudio.google.com/app/apikey"
        echo "  - Or other LLM API keys as needed"
    else
        echo "Warning: .env.example not found. Please create a .env file with your API keys."
    fi
else
    echo ".env file already exists."
fi

echo ""
echo "========================================="
echo "Installation Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your API keys"
echo "2. Run the service with: uvicorn app.main:app --reload"
echo "3. Visit http://localhost:8000/docs for API documentation"
echo ""
echo "For more information, see README.md"