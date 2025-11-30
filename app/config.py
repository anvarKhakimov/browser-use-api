"""Application configuration using Pydantic Settings."""

import os
import logging
from typing import List, Optional
from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # LLM API Keys
    browser_use_api_key: Optional[str] = Field(None, description="Browser-Use API key")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key")
    google_api_key: Optional[str] = Field(None, description="Google API key")

    # Server Configuration
    port: int = Field(8765, description="Server port")
    environment: str = Field("production", description="Environment (development/production)")
    log_level: str = Field("INFO", description="Logging level")

    # Browser Configuration
    max_concurrent_browsers: int = Field(2, ge=1, le=5, description="Maximum concurrent browser instances")
    browser_timeout: int = Field(300, ge=30, le=1200, description="Browser operation timeout in seconds (max 20 minutes)")
    max_steps: int = Field(40, ge=1, le=200, description="Maximum agent steps per task")
    headless_browser: bool = Field(True, description="Run browser in headless mode (no GUI)")

    # Rate Limiting
    rate_limit_requests: int = Field(10, ge=1, description="Maximum requests per window")
    rate_limit_window: int = Field(60, ge=1, description="Rate limit window in seconds")

    # CORS Configuration
    cors_origins: List[str] = Field(["*"], description="Allowed CORS origins")

    # Optional Settings
    anonymized_telemetry: bool = Field(False, description="Enable anonymized telemetry")
    in_docker: bool = Field(False, description="Running in Docker container")

    @model_validator(mode="after")
    def validate_api_keys(self) -> "Settings":
        """Ensure at least one LLM API key is provided."""
        api_keys = [
            self.browser_use_api_key,
            self.openai_api_key,
            self.anthropic_api_key,
            self.google_api_key
        ]

        if not any(api_keys):
            raise ValueError(
                "At least one LLM API key must be provided. "
                "Set one of: BROWSER_USE_API_KEY, OPENAI_API_KEY, "
                "ANTHROPIC_API_KEY, or GOOGLE_API_KEY"
            )

        return self

    @field_validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v

    @field_validator("environment")
    def validate_environment(cls, v: str) -> str:
        """Validate environment."""
        valid_envs = ["development", "production", "staging"]
        v = v.lower()
        if v not in valid_envs:
            raise ValueError(f"Invalid environment: {v}. Must be one of {valid_envs}")
        return v

    @field_validator("headless_browser")
    def auto_detect_headless(cls, v: bool) -> bool:
        """Auto-enable headless in Docker/Railway environments."""
        # Force headless mode in production environments
        if os.getenv("IN_DOCKER", "false").lower() == "true":
            if not v:
                logger.warning("Forcing headless mode: Docker environment detected")
            return True
        if os.getenv("RAILWAY_ENVIRONMENT"):
            if not v:
                logger.warning("Forcing headless mode: Railway environment detected")
            return True
        # Respect user setting in local environments
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"

    @property
    def chromium_args(self) -> List[str]:
        """Get Chromium browser arguments for Docker/Railway."""
        args = []
        if self.in_docker or os.getenv("IN_DOCKER", "false").lower() == "true":
            args.extend([
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--disable-setuid-sandbox"
            ])
        return args

    def get_llm_config(self) -> dict:
        """Get configuration for LLM initialization."""
        config = {}

        if self.browser_use_api_key:
            config["browser_use_api_key"] = self.browser_use_api_key
        if self.openai_api_key:
            config["openai_api_key"] = self.openai_api_key
        if self.anthropic_api_key:
            config["anthropic_api_key"] = self.anthropic_api_key
        if self.google_api_key:
            config["google_api_key"] = self.google_api_key

        return config


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()