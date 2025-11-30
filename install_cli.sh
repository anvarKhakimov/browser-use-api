#!/bin/bash

# Install Browser-Use CLI tool
# This script installs the 'bro' command-line tool

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${BOLD}${BLUE}Browser-Use CLI Installation${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Python 3
if ! command_exists python3; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    echo "Please install Python 3 before running this script"
    exit 1
fi

# Check for pip
if ! command_exists pip3 && ! command_exists pip; then
    echo -e "${RED}✗ pip is not installed${NC}"
    echo "Please install pip before running this script"
    exit 1
fi

# Determine pip command
if command_exists pip3; then
    PIP_CMD="pip3"
else
    PIP_CMD="pip"
fi

# Ask user which version to install
echo -e "${BOLD}Select installation type:${NC}"
echo "1) Python CLI with Rich formatting (recommended)"
echo "2) Simple Bash script"
echo "3) Both"
echo
read -p "Enter choice [1-3]: " choice

case $choice in
    1|3)
        echo
        echo -e "${BLUE}Installing Python CLI...${NC}"

        # Install Python dependencies
        echo "Installing dependencies..."
        $PIP_CMD install -r "$SCRIPT_DIR/cli/requirements.txt"

        # Make Python script executable
        chmod +x "$SCRIPT_DIR/cli/bro.py"

        # Create symlink for Python version
        if [ -w /usr/local/bin ]; then
            ln -sf "$SCRIPT_DIR/cli/bro.py" /usr/local/bin/bro
        else
            echo -e "${YELLOW}Need sudo permission to create symlink in /usr/local/bin${NC}"
            sudo ln -sf "$SCRIPT_DIR/cli/bro.py" /usr/local/bin/bro
        fi

        echo -e "${GREEN}✓ Python CLI installed${NC}"

        if [ "$choice" != "3" ]; then
            INSTALLED="python"
        fi
        ;;
esac

case $choice in
    2)
        echo
        echo -e "${BLUE}Installing Bash script...${NC}"

        # Make bash script executable
        chmod +x "$SCRIPT_DIR/cli/bro.sh"

        # Create symlink for Bash version
        if [ -w /usr/local/bin ]; then
            ln -sf "$SCRIPT_DIR/cli/bro.sh" /usr/local/bin/bro
        else
            echo -e "${YELLOW}Need sudo permission to create symlink in /usr/local/bin${NC}"
            sudo ln -sf "$SCRIPT_DIR/cli/bro.sh" /usr/local/bin/bro
        fi

        echo -e "${GREEN}✓ Bash script installed${NC}"
        INSTALLED="bash"
        ;;

    3)
        echo
        echo -e "${BLUE}Installing Bash script as 'bro-bash'...${NC}"

        # Make bash script executable
        chmod +x "$SCRIPT_DIR/cli/bro.sh"

        # Create symlink for Bash version with different name
        if [ -w /usr/local/bin ]; then
            ln -sf "$SCRIPT_DIR/cli/bro.sh" /usr/local/bin/bro-bash
        else
            echo -e "${YELLOW}Need sudo permission to create symlink in /usr/local/bin${NC}"
            sudo ln -sf "$SCRIPT_DIR/cli/bro.sh" /usr/local/bin/bro-bash
        fi

        echo -e "${GREEN}✓ Bash script installed as 'bro-bash'${NC}"
        INSTALLED="both"
        ;;

    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# Verify installation
echo
echo -e "${BLUE}Verifying installation...${NC}"

if command_exists bro; then
    echo -e "${GREEN}✓ 'bro' command is available${NC}"
else
    echo -e "${YELLOW}⚠ 'bro' command not found in PATH${NC}"
    echo "You may need to:"
    echo "  1. Add /usr/local/bin to your PATH"
    echo "  2. Restart your terminal"
    echo "  3. Run: source ~/.bashrc or source ~/.zshrc"
fi

if [ "$INSTALLED" = "both" ] && command_exists bro-bash; then
    echo -e "${GREEN}✓ 'bro-bash' command is available${NC}"
fi

# Show usage instructions
echo
echo -e "${BOLD}${GREEN}Installation complete!${NC}"
echo
echo -e "${BOLD}Quick Start:${NC}"
echo

if [ "$INSTALLED" = "python" ] || [ "$INSTALLED" = "both" ]; then
    echo -e "${BOLD}Python CLI Usage:${NC}"
    echo "  bro find top news on BBC"
    echo "  bro go to example.com"
    echo "  bro search for latest AI news"
    echo "  bro --help                    # Show all options"
    echo "  bro --config                  # Show configuration"
    echo "  bro --verbose <task>          # Verbose output"
    echo
fi

if [ "$INSTALLED" = "bash" ]; then
    echo -e "${BOLD}Bash Script Usage:${NC}"
    echo "  bro find top news on BBC"
    echo "  bro go to example.com"
    echo "  bro --help                    # Show help"
    echo
fi

if [ "$INSTALLED" = "both" ]; then
    echo -e "${BOLD}Bash Script Usage:${NC}"
    echo "  bro-bash find top news         # Use bash version"
    echo "  bro-bash --help               # Show bash help"
    echo
fi

echo -e "${BOLD}Configuration:${NC}"
echo "  Default API URL: http://localhost:8765"
echo
echo "  To change API URL:"

if [ "$INSTALLED" = "python" ] || [ "$INSTALLED" = "both" ]; then
    echo "    bro --set-url http://your-server:port"
    echo "    # or"
fi

echo "    export BRO_API_URL=http://your-server:port"
echo
echo -e "${BOLD}Note:${NC} Make sure the Browser-Use API service is running!"
echo "  cd $SCRIPT_DIR && uvicorn app.main:app --port 8765"
echo