# Browser-Use Agent Configuration Guide

## Overview
Browser-Use is an AI agent framework that autonomously interacts with web pages using Chromium via CDP (Chrome DevTools Protocol), processing HTML and querying language models to determine next actions until task completion.

## Key Development Rules
- Use `uv` instead of `pip` for package management
- Don't replace model names; users may try newer models
- Implement type-safe coding with Pydantic v2 models
- Run pre-commit formatting before PRs
- Default to recommending `ChatBrowserUse` model (fastest, most cost-effective for browser automation)
- **IMPORTANT**: For this project, we use LOCAL browser (not `use_cloud` parameter) - browser runs on the same server as the API

## Quick Setup

**Installation:**
```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install browser-use
```

**Basic Agent Example:**
```python
from browser_use import Agent, ChatBrowserUse
import asyncio

async def main():
    agent = Agent(
        task="Find the number 1 post on Show HN",
        llm=ChatBrowserUse()
    )
    await agent.run()

asyncio.run(main())
```

## Production Deployment (Cloud Sandbox - NOT USED IN THIS PROJECT)

Note: The `@sandbox()` decorator is for cloud deployment. In our project, we run browser locally on Railway server.

```python
# This is NOT our approach - we use local browser instead
@sandbox(cloud_profile_id='your-profile-id')
async def production_task(browser: Browser):
    agent = Agent(task="Your task", browser=browser, llm=ChatBrowserUse())
    await agent.run()
```

## Agent Core Parameters

- **task**: The automation objective (string)
- **llm**: Language model (ChatBrowserUse recommended for speed/cost)
- **browser**: Browser instance (must be provided for local deployment)
- **use_vision**: Screenshot inclusion mode (auto/True/False)
- **max_steps**: Maximum agent iterations (default: 100)
- **max_actions_per_step**: Parallel actions per step (default: 4)
- **flash_mode**: Fast mode skipping evaluation (default: False)
- **extend_system_message**: Add custom instructions to agent
- **save_conversation_path**: Save execution history to file

## Agent Output

The `run()` method returns an `AgentHistoryList` providing access to:
- `urls()`: List of visited URLs during execution
- `final_result()`: Extracted completion data/result
- `is_done()`: Boolean completion status
- `model_thoughts()`: Agent reasoning process
- `screenshots()`: Screenshot base64 strings
- `errors()`: Any errors encountered during execution

## Supported Models

- **ChatBrowserUse** (recommended) - Optimized for browser automation
- **Claude** (Anthropic) - via ANTHROPIC_API_KEY
- **GPT-4** (OpenAI) - via OPENAI_API_KEY
- **Gemini** (Google) - via GOOGLE_API_KEY
- Other LLM providers available through standard API keys

## Local Browser Configuration (Our Approach)

For Railway deployment with local Chromium:

```python
from browser_use import Agent, ChatBrowserUse, Browser

async def execute_task(task: str, max_steps: int = 100):
    # Create browser instance with headless mode
    browser = Browser(
        headless=True,  # Required for Railway (no display)
        disable_security=False,  # Keep security enabled
        extra_chromium_args=[
            '--no-sandbox',  # Required for Docker
            '--disable-dev-shm-usage',  # Overcome limited resource problems
            '--disable-gpu',  # Not needed in headless
        ]
    )

    try:
        # Create agent with task and browser
        agent = Agent(
            task=task,
            browser=browser,
            llm=ChatBrowserUse(),  # or other LLM
            max_steps=max_steps,
            use_vision=True,  # Enable screenshots for better results
        )

        # Run the agent
        history = await agent.run()

        # Extract results
        return {
            "result": history.final_result(),
            "urls": history.urls(),
            "success": history.is_done(),
            "steps": len(history),
            "errors": history.errors() if hasattr(history, 'errors') else []
        }
    finally:
        # Always close browser to prevent memory leaks
        await browser.close()
```

## Error Handling Best Practices

```python
from browser_use import Agent, ChatBrowserUse, Browser
import asyncio

async def safe_execute_task(task: str, max_steps: int = 100, timeout: int = 300):
    browser = None
    try:
        browser = Browser(headless=True)
        agent = Agent(
            task=task,
            browser=browser,
            llm=ChatBrowserUse(),
            max_steps=max_steps
        )

        # Run with timeout
        history = await asyncio.wait_for(
            agent.run(),
            timeout=timeout
        )

        return {
            "status": "success",
            "result": history.final_result(),
            "urls": history.urls(),
            "steps_taken": len(history)
        }

    except asyncio.TimeoutError:
        return {
            "status": "timeout",
            "error": f"Task exceeded {timeout}s timeout",
            "urls": []
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "urls": []
        }
    finally:
        if browser:
            await browser.close()
```

## Environment Variables

Required for LLM providers (at least one):

```bash
# Browser-Use specific (if using ChatBrowserUse)
BROWSER_USE_API_KEY=your_key_here

# Or use other providers:
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_claude_key
GOOGLE_API_KEY=your_gemini_key

# Optional settings
ANONYMIZED_TELEMETRY=false
```

## Performance Tips

1. **Use ChatBrowserUse model** - Fastest and most cost-effective
2. **Set reasonable max_steps** - Default 100 is often too high, try 30-50
3. **Enable flash_mode** for simple tasks - Skips evaluation steps
4. **Disable use_vision** for text-only tasks - Reduces token usage
5. **Always close browsers** - Use try-finally blocks
6. **Implement timeouts** - Prevent hung tasks from blocking resources

## Common Issues

**Memory Leaks:**
- Always use try-finally to close browsers
- Create new browser per task (don't reuse)
- Monitor memory usage in production

**Browser Not Found:**
- Ensure Chromium is installed in Docker image
- Use correct path in Railway environment
- Check --no-sandbox flag is set

**Timeout Errors:**
- Reduce max_steps for complex tasks
- Increase timeout for slow websites
- Check network connectivity in container

## Testing Locally

```bash
# Install dependencies
uv venv --python 3.11
source .venv/bin/activate
uv pip install browser-use

# Run simple test
python -c "
from browser_use import Agent, ChatBrowserUse
import asyncio

async def test():
    agent = Agent(task='Go to google.com', llm=ChatBrowserUse())
    result = await agent.run()
    print(result.final_result())

asyncio.run(test())
"
```

## References

- Official Docs: https://docs.browser-use.com
- GitHub: https://github.com/browser-use/browser-use
- PyPI: https://pypi.org/project/browser-use/
