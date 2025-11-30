"""Main FastAPI application."""

import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__
from app.config import get_settings
from app.api.v1 import endpoints
from app.middleware.error_handler import (
    ErrorHandlerMiddleware,
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler,
)
from app.middleware.rate_limit import create_rate_limit_middleware
from app.services.browser_manager import get_browser_manager
from app.utils.logger import setup_logging, get_logger

# Initialize logging
setup_logging()
logger = get_logger(__name__)

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.

    Handles startup and shutdown tasks.
    """
    # Startup
    logger.info(f"Starting Browser-Use API Service v{__version__}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Max concurrent browsers: {settings.max_concurrent_browsers}")

    # Verify LLM configuration
    llm_config = settings.get_llm_config()
    if llm_config:
        logger.info(f"LLM providers configured: {list(llm_config.keys())}")
    else:
        logger.error("No LLM API keys configured!")

    # Set environment variables for Browser-Use if needed
    if settings.browser_use_api_key:
        os.environ["BROWSER_USE_API_KEY"] = settings.browser_use_api_key
    if settings.openai_api_key:
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
    if settings.anthropic_api_key:
        os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
    if settings.google_api_key:
        os.environ["GOOGLE_API_KEY"] = settings.google_api_key

    # Disable telemetry if configured
    if not settings.anonymized_telemetry:
        os.environ["ANONYMIZED_TELEMETRY"] = "false"

    # Store startup time
    app.state.startup_time = time.time()

    logger.info("Browser-Use API Service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Browser-Use API Service...")

    # Clean up browser instances
    browser_manager = get_browser_manager()
    await browser_manager.cleanup_all()

    logger.info("Browser-Use API Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Browser-Use API Service",
    description="REST API service for web information extraction using Browser-Use agents",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add middleware

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-Response-Time"],
)

# Error handler
app.add_middleware(ErrorHandlerMiddleware)

# Rate limiting
app.add_middleware(create_rate_limit_middleware)

# Exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(endpoints.router)


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Browser-Use API Service",
        "version": __version__,
        "status": "running",
        "environment": settings.environment,
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
        },
        "endpoints": {
            "search": "/api/v1/search",
            "health": "/api/v1/health",
            "status": "/api/v1/status",
        }
    }


# Health check at root level (for simpler monitoring)
@app.get("/health", tags=["monitoring"])
async def health_check():
    """Simple health check endpoint."""
    browser_manager = get_browser_manager()
    uptime = time.time() - app.state.startup_time if hasattr(app.state, "startup_time") else 0

    return {
        "status": "ok" if browser_manager.is_available else "degraded",
        "version": __version__,
        "uptime_seconds": uptime,
        "active_browsers": browser_manager.active_count,
        "max_browsers": settings.max_concurrent_browsers,
    }


# Custom 404 handler
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors with custom response."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "NotFound",
            "message": f"The requested path '{request.url.path}' was not found",
            "available_endpoints": [
                "/",
                "/health",
                "/api/v1/search",
                "/api/v1/health",
                "/api/v1/status",
                "/docs",
                "/redoc",
            ]
        }
    )


if __name__ == "__main__":
    # For development/testing only
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )