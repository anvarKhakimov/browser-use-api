# Browser-Use CLI Quick Start Guide

The `bro` command-line tool provides a simple way to interact with the Browser-Use API service directly from your terminal.

## Installation (30 seconds)

### Option 1: Quick Install (Recommended)

```bash
# Run the installer
./install_cli.sh

# Choose option 1 for Python CLI with Rich formatting
# Enter your password when prompted for sudo
```

### Option 2: Manual Symlink

```bash
# Make the Python script executable
chmod +x cli/bro.py

# Create symlink (may need sudo)
sudo ln -sf "$(pwd)/cli/bro.py" /usr/local/bin/bro
```

### Option 3: Shell Alias (Simplest)

```bash
# Add alias to your shell config
./cli/install_alias.sh

# Reload shell config
source ~/.zshrc  # or ~/.bashrc
```

## Usage Examples

### Basic Commands

```bash
# Find information
bro find top news on BBC
bro what's the weather in San Francisco

# Navigate websites
bro go to github.com and search for browser automation
bro take a screenshot of example.com

# Search content
bro search for latest AI news on HackerNews
bro find trending repos on GitHub today
```

### Advanced Options

```bash
# Show help
bro --help

# View configuration
bro --config

# Verbose output with details
bro --verbose find latest tech news

# JSON output for scripting
bro --json find weather | jq '.result'

# Configure API endpoint
bro --set-url http://localhost:8765
bro --set-timeout 180
bro --set-steps 15
```

## Before You Start

1. **Start the Browser-Use API service:**
   ```bash
   uvicorn app.main:app --port 8765
   ```

2. **Test the CLI:**
   ```bash
   bro find current time in Tokyo
   ```

## Expected Output

```
━━━━━━━━━━━━━━━━ Task: find top news on BBC ━━━━━━━━━━━━━━━━

✓ Task completed successfully!

┌─────────── Result ───────────┐
│ Top news: UK government      │
│ announces new climate plan   │
└───────────────────────────────┘

• Steps: 3 | Time: 8.45s

URLs visited:
  https://bbc.com
```

## Troubleshooting

### "command not found"
- Run: `source ~/.zshrc` or restart terminal
- Check: `which bro` to see if it's in PATH

### "Cannot connect to Browser-Use API"
- Ensure the API service is running on port 8765
- Check: `curl http://localhost:8765/docs`

### "Permission denied"
- Use sudo for installation: `sudo ./install_cli.sh`

## Features

- 🎨 **Rich formatting** - Colorized output with progress indicators
- ⚡ **Fast** - Direct API integration
- 🔧 **Configurable** - Persistent settings
- 📊 **Flexible output** - Human-readable or JSON
- 🛠️ **Multiple implementations** - Python or Bash

## Files

- `cli/bro.py` - Main Python CLI implementation
- `cli/bro.sh` - Bash script alternative
- `cli/requirements.txt` - Python dependencies
- `cli/README.md` - Detailed documentation
- `install_cli.sh` - Installation script

## Uninstall

```bash
# Remove symlink
sudo rm /usr/local/bin/bro

# Remove config
rm ~/.broconfig

# Remove alias (if used)
# Edit ~/.zshrc or ~/.bashrc and remove the bro alias
```