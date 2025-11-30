"""Response models for the API."""

from typing import List, Literal, Optional, Any
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class SearchResponse(BaseModel):
    """Response model for successful search/extraction tasks."""

    result: Optional[str] = Field(
        None,
        description="The extracted result or answer from the web task"
    )

    urls_visited: List[str] = Field(
        default_factory=list,
        description="List of URLs visited during task execution"
    )

    status: Literal["success", "failed", "timeout"] = Field(
        ...,
        description="Task completion status"
    )

    error_message: Optional[str] = Field(
        None,
        description="Error message if task failed"
    )

    execution_time: float = Field(
        ...,
        description="Total execution time in seconds"
    )

    steps_taken: int = Field(
        ...,
        description="Number of steps taken by the agent"
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of task completion"
    )

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        json_schema_extra={
            "examples": [
                {
                    "result": "The top repository is 'awesome-project' with 5.2k stars today",
                    "urls_visited": [
                        "https://github.com/trending",
                        "https://github.com/user/awesome-project"
                    ],
                    "status": "success",
                    "error_message": None,
                    "execution_time": 15.3,
                    "steps_taken": 8,
                    "timestamp": "2024-01-01T12:00:00Z"
                }
            ]
        }
    )


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    status: Literal["ok", "degraded", "unhealthy"] = Field(
        ...,
        description="Overall health status of the service"
    )

    version: str = Field(
        ...,
        description="API version"
    )

    uptime: float = Field(
        ...,
        description="Service uptime in seconds"
    )

    browser_available: bool = Field(
        ...,
        description="Whether browser automation is available"
    )

    active_browsers: int = Field(
        0,
        description="Number of currently active browser instances"
    )

    max_browsers: int = Field(
        2,
        description="Maximum allowed browser instances"
    )

    environment: str = Field(
        ...,
        description="Current environment (production/development)"
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Health check timestamp"
    )


class ErrorResponse(BaseModel):
    """Response model for API errors."""

    error: str = Field(
        ...,
        description="Error type or code"
    )

    message: str = Field(
        ...,
        description="Human-readable error message"
    )

    detail: Optional[Any] = Field(
        None,
        description="Additional error details"
    )

    request_id: Optional[str] = Field(
        None,
        description="Request tracking ID"
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp"
    )

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        json_schema_extra={
            "examples": [
                {
                    "error": "ValidationError",
                    "message": "Invalid request parameters",
                    "detail": {"task": ["Field is required"]},
                    "request_id": "req_123456",
                    "timestamp": "2024-01-01T12:00:00Z"
                },
                {
                    "error": "RateLimitExceeded",
                    "message": "Too many requests. Please try again later.",
                    "detail": {"retry_after": 60},
                    "request_id": "req_789012",
                    "timestamp": "2024-01-01T12:00:00Z"
                }
            ]
        }
    )