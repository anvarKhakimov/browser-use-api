#!/bin/bash

# Quick alias installation for Browser-Use CLI
# Adds a simple alias to your shell configuration

# Detect shell
if [ -n "$ZSH_VERSION" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
    SHELL_NAME="zsh"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
    SHELL_NAME="bash"
else
    echo "Unsupported shell. Please add the alias manually."
    exit 1
fi

# Create the alias
ALIAS_CONTENT='
# Browser-Use CLI alias
alias bro='"'"'function _bro() {
    local TASK="$*"
    echo -e "\033[1m\033[34mTask:\033[0m $TASK"
    echo -e "\033[32m⏳ Processing...\033[0m"
    local RESPONSE=$(curl -s -X POST http://localhost:8765/api/v1/search \
        -H "Content-Type: application/json" \
        -d "{\"task\": \"$TASK\", \"max_steps\": 10, \"timeout\": 120}")

    if [ -z "$RESPONSE" ]; then
        echo -e "\033[31m✗ Error: No response from API\033[0m"
        return 1
    fi

    local STATUS=$(echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('"'"'status'"'"', '"'"'error'"'"'))" 2>/dev/null)

    if [ "$STATUS" = "success" ]; then
        echo -e "\033[32m✓ Success!\033[0m"
        echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('"'"'result'"'"', '"'"'No result'"'"'))"
        echo -e "\033[2m• Steps: $(echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('"'"'steps_taken'"'"', 0))") | Time: $(echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"{d.get('"'"'execution_time'"'"', 0):.1f}\")s\033[0m"
    else
        echo -e "\033[31m✗ Failed\033[0m"
        echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('"'"'error_message'"'"', '"'"'Unknown error'"'"'))"
    fi
}; _bro'"'"'
'

# Check if alias already exists
if grep -q "alias bro=" "$SHELL_CONFIG" 2>/dev/null; then
    echo "⚠ Alias 'bro' already exists in $SHELL_CONFIG"
    echo "Please remove it first if you want to reinstall."
    exit 1
fi

# Add alias to shell config
echo "$ALIAS_CONTENT" >> "$SHELL_CONFIG"

echo "✓ Alias added to $SHELL_CONFIG"
echo ""
echo "To activate the alias, run:"
echo "  source $SHELL_CONFIG"
echo ""
echo "Or restart your terminal."
echo ""
echo "Usage:"
echo "  bro find top news on BBC"
echo "  bro go to example.com"
echo "  bro search for latest AI news"