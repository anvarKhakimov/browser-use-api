"""Browser-Use agent service for task execution."""

import asyncio
import logging
import time
from typing import Dict, Any, Optional
from uuid import uuid4

from browser_use import Agent, ChatBrowserUse, ChatGoogle
from browser_use.agent.views import AgentHistoryList

from app.config import get_settings
from app.services.browser_manager import get_browser_manager

logger = logging.getLogger(__name__)


class AgentService:
    """Service for executing web tasks using Browser-Use agents."""

    def __init__(self):
        """Initialize agent service."""
        self.settings = get_settings()
        self.browser_manager = get_browser_manager()

    def _get_llm(self):
        """
        Get the appropriate LLM instance based on available API keys.

        Priority order:
        1. Google Gemini (GOOGLE_API_KEY) - Recommended, cost-effective
        2. ChatBrowserUse (BROWSER_USE_API_KEY) - Fast, optimized for browser tasks
        3. Anthropic Claude (ANTHROPIC_API_KEY)
        4. OpenAI GPT (OPENAI_API_KEY)

        Returns:
            LLM instance

        Raises:
            ValueError: If no valid LLM can be configured
        """
        # Priority 1: Google Gemini (User's preference)
        if self.settings.google_api_key:
            try:
                logger.info("Using Google Gemini LLM (gemini-2.5-flash)")
                # Use browser-use's ChatGoogle which properly implements the provider property
                return ChatGoogle(
                    model="gemini-2.5-flash",
                    api_key=self.settings.google_api_key,
                    temperature=0.5,
                    max_output_tokens=8096,
                )
            except Exception as e:
                logger.error(f"Failed to initialize Gemini LLM: {e}")
                logger.info("Falling back to next available LLM")

        # Priority 2: ChatBrowserUse (fastest, most cost-effective for browser tasks)
        if self.settings.browser_use_api_key:
            logger.info("Using ChatBrowserUse LLM")
            return ChatBrowserUse()

        # Priority 3: Anthropic Claude
        if self.settings.anthropic_api_key:
            try:
                from langchain_anthropic import ChatAnthropic
                logger.info("Using Anthropic Claude LLM")
                return ChatAnthropic(
                    model="claude-3-5-sonnet-20241022",
                    api_key=self.settings.anthropic_api_key,
                    temperature=0.5,
                )
            except ImportError:
                logger.warning("langchain-anthropic not installed, skipping Claude")
            except Exception as e:
                logger.error(f"Failed to initialize Claude LLM: {e}")

        # Priority 4: OpenAI GPT
        if self.settings.openai_api_key:
            try:
                from langchain_openai import ChatOpenAI
                logger.info("Using OpenAI GPT-4 LLM")
                return ChatOpenAI(
                    model="gpt-4o",
                    api_key=self.settings.openai_api_key,
                    temperature=0.5,
                )
            except ImportError:
                logger.warning("langchain-openai not installed, skipping OpenAI")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI LLM: {e}")

        # No valid LLM could be configured
        raise ValueError(
            "No LLM could be initialized. Please ensure you have:\n"
            "1. Valid API key in environment (GOOGLE_API_KEY recommended)\n"
            "2. Check logs above for specific initialization errors\n"
            "Supported API keys: GOOGLE_API_KEY, BROWSER_USE_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY"
        )

    async def execute_task(
        self,
        task: str,
        max_steps: int = 40,
        timeout: int = 300,
        use_vision: bool = True,
        flash_mode: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute a web task using Browser-Use agent.

        Args:
            task: The task description to execute
            max_steps: Maximum number of steps the agent can take
            timeout: Timeout in seconds for the entire execution
            use_vision: Whether to use visual analysis (screenshots)
            flash_mode: Whether to use flash mode (faster but less accurate)

        Returns:
            Dictionary containing task results and metadata
        """
        task_id = str(uuid4())
        start_time = time.time()

        logger.info(
            f"Starting task {task_id}: '{task[:100]}...' "
            f"(max_steps={max_steps}, timeout={timeout}s, vision={use_vision}, flash={flash_mode})"
        )

        try:
            # Get browser instance from manager
            async with self.browser_manager.get_browser(task_id) as browser:
                # Create agent with Browser-Use
                agent = Agent(
                    task=task,
                    browser=browser,
                    llm=self._get_llm(),
                    max_steps=max_steps,
                    use_vision=use_vision,
                    max_actions_per_step=4,  # Default parallelism
                    flash_mode=flash_mode,
                )

                # Execute with timeout
                try:
                    history: AgentHistoryList = await asyncio.wait_for(
                        agent.run(),
                        timeout=timeout
                    )

                    execution_time = time.time() - start_time

                    # Extract results from history
                    result = {
                        "status": "success",
                        "result": history.final_result() if hasattr(history, 'final_result') else str(history),
                        "urls_visited": history.urls() if hasattr(history, 'urls') else [],
                        "steps_taken": len(history) if history else 0,
                        "execution_time": execution_time,
                        "task_id": task_id,
                        "is_done": history.is_done() if hasattr(history, 'is_done') else True,
                        "errors": history.errors() if hasattr(history, 'errors') else [],
                    }

                    # Add model thoughts if available (for debugging)
                    if hasattr(history, 'model_thoughts'):
                        result["model_thoughts"] = history.model_thoughts()

                    logger.info(
                        f"Task {task_id} completed successfully in {execution_time:.2f}s "
                        f"({result['steps_taken']} steps, {len(result['urls_visited'])} URLs)"
                    )

                    return result

                except asyncio.TimeoutError:
                    execution_time = time.time() - start_time
                    logger.warning(f"Task {task_id} timed out after {timeout}s")

                    return {
                        "status": "timeout",
                        "result": None,
                        "urls_visited": [],
                        "steps_taken": 0,
                        "execution_time": execution_time,
                        "task_id": task_id,
                        "error_message": f"Task execution exceeded timeout of {timeout} seconds",
                    }

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)

            logger.error(f"Task {task_id} failed: {error_msg}", exc_info=True)

            return {
                "status": "failed",
                "result": None,
                "urls_visited": [],
                "steps_taken": 0,
                "execution_time": execution_time,
                "task_id": task_id,
                "error_message": error_msg,
            }

    async def validate_browser_availability(self) -> bool:
        """
        Validate that browser automation is available.

        Returns:
            True if browser can be created, False otherwise
        """
        try:
            # Quick test to create and close a browser
            async with self.browser_manager.get_browser("health-check") as browser:
                # Browser created successfully
                return True
        except Exception as e:
            logger.error(f"Browser availability check failed: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get agent service status."""
        return {
            "llm_configured": bool(self.settings.get_llm_config()),
            "browser_manager": self.browser_manager.get_status(),
            "default_max_steps": self.settings.max_steps,
            "default_timeout": self.settings.browser_timeout,
        }


# Global agent service instance
_agent_service: Optional[AgentService] = None


def get_agent_service() -> AgentService:
    """Get or create the global agent service instance."""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service