# Browser-Use CLI Tool (`bro`)

A command-line interface for interacting with the Browser-Use API service. Execute browser automation tasks directly from your terminal.

## Features

- **Simple Syntax**: Natural language commands like `bro find weather in London`
- **Rich Output**: Colorized, formatted results with progress indicators
- **Configurable**: Customize API URL, timeout, and other settings
- **Multiple Implementations**: Choose between Python (feature-rich) or Bash (lightweight)
- **Verbose Mode**: Get detailed information about actions performed
- **Persistent Configuration**: Save your preferences

## Installation

### Quick Install

```bash
cd /path/to/browser-use-api
./install_cli.sh
```

The installer will prompt you to choose:
1. Python CLI with Rich formatting (recommended)
2. Simple Bash script
3. Both versions

### Manual Installation

#### Python CLI

```bash
# Install dependencies
pip install httpx rich

# Make executable
chmod +x cli/bro.py

# Create symlink
sudo ln -sf "$(pwd)/cli/bro.py" /usr/local/bin/bro
```

#### Bash Script

```bash
# Make executable
chmod +x cli/bro.sh

# Create symlink
sudo ln -sf "$(pwd)/cli/bro.sh" /usr/local/bin/bro
```

## Usage

### Basic Commands

```bash
# Find information
bro find top news on BBC
bro what's the weather in San Francisco

# Navigate websites
bro go to example.com
bro go to github.com and search for browser automation

# Search for content
bro search for latest AI news on HackerNews
bro find top trending repos on GitHub today
```

### Python CLI Options

```bash
# Show help
bro --help

# Show current configuration
bro --config

# Set API URL
bro --set-url http://localhost:8765

# Set timeout (seconds)
bro --set-timeout 180

# Set maximum steps
bro --set-steps 15

# Verbose output
bro --verbose find latest tech news

# Combine task with options
bro --verbose search for Python tutorials
```

### Bash Script Options

```bash
# Show help
bro --help

# Set via environment variables
export BRO_API_URL=http://localhost:8765
export BRO_MAX_STEPS=10
export BRO_TIMEOUT=120

# Execute task
bro find latest news
```

## Configuration

### Python CLI Configuration

Configuration is stored in `~/.broconfig`:

```json
{
  "api_url": "http://localhost:8765",
  "max_steps": 10,
  "timeout": 120
}
```

Environment variable `BRO_API_URL` overrides the config file.

### Bash Script Configuration

Use environment variables:

```bash
export BRO_API_URL=http://localhost:8765/api/v1/search
export BRO_MAX_STEPS=10
export BRO_TIMEOUT=120
```

## Output Format

### Success Response

```
✓ Task completed successfully!

┌─────────── Result ───────────┐
│ Top news: UK government      │
│ announces new climate plan   │
└───────────────────────────────┘

• Steps: 3 | Time: 8.45s

URLs visited:
  https://bbc.com
```

### Verbose Output

With `--verbose` flag, you get additional information:

- Detailed metadata table
- List of actions performed
- Model information
- Extended timing details

## Examples

### Information Retrieval

```bash
# News
bro find latest tech news on TechCrunch

# Weather information
bro what's the weather forecast for tomorrow in NYC

# Research
bro find top rated restaurants in San Francisco
```

### Web Navigation

```bash
# Take screenshots
bro go to twitter.com and take a screenshot

# Form submission
bro go to example.com/contact and fill the form

# Multi-step tasks
bro go to amazon.com, search for laptops, and find the best rated one
```

### Research Tasks

```bash
# News aggregation
bro find top 5 tech news from TechCrunch today

# GitHub exploration
bro find most starred Python repos this week on GitHub

# Documentation lookup
bro find React hooks documentation
```

## Troubleshooting

### Connection Error

```
Cannot connect to Browser-Use API at http://localhost:8765
```

**Solution**: Ensure the Browser-Use API service is running:

```bash
cd /path/to/browser-use-api
uvicorn app.main:app --port 8765
```

### Command Not Found

```
bro: command not found
```

**Solution**:
1. Add `/usr/local/bin` to your PATH
2. Restart your terminal
3. Or source your shell config: `source ~/.bashrc`

### Permission Denied

```
Permission denied: /usr/local/bin/bro
```

**Solution**: Run the installer with proper permissions:

```bash
sudo ./install_cli.sh
```

## Advanced Usage

### Chaining with Shell Commands

```bash
# Save output to file
bro find weather in Tokyo > weather.txt

# Process with jq (Python CLI with --json flag)
bro --json find weather | jq '.result'

# Use in scripts
NEWS=$(bro find top tech news | head -1)
echo "Latest news: $NEWS"
```

### Using in Scripts

```python
#!/usr/bin/env python3
import subprocess
import json

def get_browser_result(task):
    result = subprocess.run(
        ['bro', '--json', task],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)

# Use the function
data = get_browser_result("find weather in Paris")
print(f"Status: {data['status']}")
print(f"Result: {data['result']}")
```

## Uninstallation

### Remove Symlinks

```bash
sudo rm /usr/local/bin/bro
sudo rm /usr/local/bin/bro-bash  # if installed
```

### Remove Configuration

```bash
rm ~/.broconfig
```

### Uninstall Python Dependencies

```bash
pip uninstall httpx rich
```

## Contributing

Feel free to submit issues or pull requests to improve the CLI tool.

## License

Same as the Browser-Use API project.