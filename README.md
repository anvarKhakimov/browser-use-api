# Browser-Use API Service

A production-ready REST API service for autonomous web browsing and information extraction using AI agents.

## Features

- **AI-Powered Web Automation**: Navigate websites and extract information autonomously
- **Simple REST API**: Easy-to-use HTTP endpoints built with FastAPI
- **Multiple LLM Support**: Google Gemini (recommended), OpenAI, Anthropic, Browser-Use
- **Production Ready**: Includes rate limiting, error handling, and health monitoring
- **Docker Support**: Containerized deployment for Railway, Render, or any platform
- **CLI Tool**: Interactive command-line interface included

## Quick Start

### 1. Install
```bash
chmod +x install.sh
./install.sh
```

### 2. Configure
```bash
cp .env.example .env
# Add your API key to .env:
# GOOGLE_API_KEY=your_key_here  (Get it: https://aistudio.google.com/app/apikey)
```

### 3. Run
```bash
./start.sh
```

API will be available at `http://localhost:8765`

## API Usage

### Execute a Task
```bash
curl -X POST http://localhost:8765/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "task": "What are the top stories on Hacker News today?"
  }'
```

### Response
```json
{
  "result": "The top stories include: 1) New AI framework released...",
  "status": "success",
  "urls_visited": ["https://news.ycombinator.com"],
  "execution_time": 8.5,
  "steps_taken": 3
}
```

### Python Example
```python
import requests

response = requests.post(
    "http://localhost:8765/api/v1/search",
    json={"task": "Find the current weather in San Francisco"}
)
print(response.json()["result"])
```

## CLI Tool

Interactive command-line interface for quick tasks:

```bash
# Install CLI
./install_cli.sh

# Use it
bro find top news on BBC
bro what's the weather in Tokyo
```

See [QUICK_START_CLI.md](QUICK_START_CLI.md) for details.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google Gemini API key (recommended) | - |
| `OPENAI_API_KEY` | OpenAI API key (alternative) | - |
| `ANTHROPIC_API_KEY` | Anthropic API key (alternative) | - |
| `PORT` | Server port | `8765` |
| `MAX_CONCURRENT_BROWSERS` | Max parallel browser instances | `2` |
| `MAX_STEPS` | Max steps per task | `40` |
| `BROWSER_TIMEOUT` | Task timeout in seconds | `300` |

See `.env.example` for all options.

## Docker Deployment

### Build and Run
```bash
docker build -t browser-use-api .
docker run -d -p 8765:8765 \
  -e GOOGLE_API_KEY=your_key \
  browser-use-api
```

### Railway/Render
1. Connect your GitHub repository
2. Set environment variable: `GOOGLE_API_KEY`
3. Deploy (Dockerfile will be detected automatically)

## Documentation

- **API Endpoints**: Visit `http://localhost:8765/docs` (Swagger UI)
- **CLI Guide**: [QUICK_START_CLI.md](QUICK_START_CLI.md)
- **Agent Patterns**: [docs/AGENTS.md](docs/AGENTS.md)

## Project Structure

```
browser-use-api/
├── app/                    # Main application
│   ├── api/               # API endpoints
│   ├── services/          # Business logic
│   ├── middleware/        # Rate limiting, error handling
│   └── models/            # Request/response models
├── cli/                   # CLI tools
├── docs/                  # Additional documentation
├── .env.example          # Environment template
├── Dockerfile            # Container configuration
└── install.sh            # Quick installation script
```

## Development

### Manual Setup
```bash
# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv --python 3.11
source .venv/bin/activate

# Install dependencies
uv sync

# Run with auto-reload
uvicorn app.main:app --reload --port 8765
```

### Debug Mode
Set `HEADLESS_BROWSER=false` in `.env` to see browser window during development.

## Common Issues

**Browser not starting?**
- Ensure Chromium is installed (included in Docker image)

**Out of memory?**
- Reduce `MAX_CONCURRENT_BROWSERS` to `1`

**Task timeout?**
- Increase `BROWSER_TIMEOUT` or simplify the task

## Tech Stack

- **Python 3.11+** with FastAPI and Pydantic v2
- **Browser-Use** for autonomous web navigation
- **Google Gemini** as recommended LLM provider
- **UV** for fast dependency management
- **Docker** with Chromium for deployment

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

Built with:
- [Browser-Use](https://github.com/browser-use/browser-use) - AI Browser Automation
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Web Framework
- [Google Gemini](https://ai.google.dev/) - LLM Provider
