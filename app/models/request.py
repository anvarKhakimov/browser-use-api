"""Request models for the API."""

from typing import Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request model for web search/extraction tasks."""

    task: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The task or query to execute on the web",
        examples=["Find the top news on Hacker News", "Get product prices from amazon.com"]
    )

    max_steps: int = Field(
        40,
        ge=1,
        le=200,
        description="Maximum number of steps the agent can take",
    )

    timeout: Optional[int] = Field(
        300,
        ge=30,
        le=600,
        description="Timeout in seconds for the entire task execution",
    )

    use_vision: bool = Field(
        True,
        description="Whether to use visual analysis (screenshots) for better results",
    )

    flash_mode: bool = Field(
        False,
        description="Enable flash mode to skip evaluation steps (faster but less accurate)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "task": "Find the top 3 trending repositories on GitHub today",
                    "max_steps": 40,
                    "timeout": 300,
                    "use_vision": True,
                    "flash_mode": False
                },
                {
                    "task": "What's the current weather in Tokyo?",
                    "max_steps": 20,
                    "timeout": 120,
                    "use_vision": False,
                    "flash_mode": True
                }
            ]
        }
    }