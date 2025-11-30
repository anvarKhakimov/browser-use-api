"""API v1 endpoints."""

import time
from uuid import uuid4
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.models.request import SearchRequest
from app.models.response import SearchResponse, HealthResponse, ErrorResponse
from app.services.agent_service import get_agent_service
from app.services.browser_manager import get_browser_manager
from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/api/v1", tags=["v1"])

# Track service start time for uptime calculation
SERVICE_START_TIME = time.time()


@router.post(
    "/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        429: {"model": ErrorResponse, "description": "Rate Limit Exceeded"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
        503: {"model": ErrorResponse, "description": "Service Unavailable"},
    },
    summary="Execute Web Search/Extraction Task",
    description="Execute a web automation task using Browser-Use agent to extract information from websites."
)
async def search(request: SearchRequest, req: Request) -> SearchResponse:
    """
    Execute a web search/extraction task.

    This endpoint uses Browser-Use agents to autonomously navigate web pages
    and extract information based on the provided task description.

    Args:
        request: Search request with task details
        req: FastAPI request object for tracking

    Returns:
        SearchResponse with extracted results

    Raises:
        HTTPException: If service is unavailable or task fails
    """
    # Generate request ID for tracking
    request_id = req.state.request_id if hasattr(req.state, "request_id") else str(uuid4())

    logger.info(
        f"[{request_id}] Received search request: task='{request.task[:100]}...', "
        f"max_steps={request.max_steps}, timeout={request.timeout}s"
    )

    # Check if browser manager has available slots
    browser_manager = get_browser_manager()
    if not browser_manager.is_available:
        logger.warning(f"[{request_id}] No browser slots available")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "ServiceUnavailable",
                "message": "No browser slots available. Please try again later.",
                "active_browsers": browser_manager.active_count,
                "max_browsers": browser_manager.settings.max_concurrent_browsers,
                "request_id": request_id,
            }
        )

    try:
        # Execute task
        agent_service = get_agent_service()
        result = await agent_service.execute_task(
            task=request.task,
            max_steps=request.max_steps,
            timeout=request.timeout or 300,
            use_vision=request.use_vision,
            flash_mode=request.flash_mode,
        )

        # Build response
        response = SearchResponse(
            result=result.get("result", ""),
            urls_visited=result.get("urls_visited", []),
            status=result.get("status", "failed"),
            error_message=result.get("error_message"),
            execution_time=result.get("execution_time", 0),
            steps_taken=result.get("steps_taken", 0),
        )

        logger.info(
            f"[{request_id}] Search completed: status={response.status}, "
            f"steps={response.steps_taken}, time={response.execution_time:.2f}s"
        )

        return response

    except Exception as e:
        logger.error(f"[{request_id}] Search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalError",
                "message": f"Task execution failed: {str(e)}",
                "request_id": request_id,
            }
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check the health status of the API service and browser availability."
)
async def health() -> HealthResponse:
    """
    Health check endpoint.

    Returns the current health status of the service including:
    - Overall service status
    - Browser availability
    - Active browser count
    - Service uptime

    Returns:
        HealthResponse with service health information
    """
    settings = get_settings()
    browser_manager = get_browser_manager()
    agent_service = get_agent_service()

    # Check browser availability
    browser_available = await agent_service.validate_browser_availability()

    # Calculate uptime
    uptime = time.time() - SERVICE_START_TIME

    # Determine overall status
    if not browser_available:
        status = "unhealthy"
    elif browser_manager.active_count >= settings.max_concurrent_browsers:
        status = "degraded"
    else:
        status = "ok"

    response = HealthResponse(
        status=status,
        version="1.0.0",
        uptime=uptime,
        browser_available=browser_available,
        active_browsers=browser_manager.active_count,
        max_browsers=settings.max_concurrent_browsers,
        environment=settings.environment,
    )

    logger.debug(
        f"Health check: status={response.status}, "
        f"browsers={response.active_browsers}/{response.max_browsers}"
    )

    return response


@router.get(
    "/status",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Service Status",
    description="Get detailed status information about the service."
)
async def status() -> Dict[str, Any]:
    """
    Detailed status endpoint.

    Provides comprehensive information about:
    - Service configuration
    - Browser manager status
    - Agent service status

    Returns:
        Dictionary with detailed status information
    """
    settings = get_settings()
    browser_manager = get_browser_manager()
    agent_service = get_agent_service()

    return {
        "service": {
            "version": "1.0.0",
            "environment": settings.environment,
            "uptime_seconds": time.time() - SERVICE_START_TIME,
        },
        "configuration": {
            "max_concurrent_browsers": settings.max_concurrent_browsers,
            "browser_timeout": settings.browser_timeout,
            "default_max_steps": settings.max_steps,
            "rate_limit": {
                "requests": settings.rate_limit_requests,
                "window_seconds": settings.rate_limit_window,
            },
        },
        "browser_manager": browser_manager.get_status(),
        "agent_service": agent_service.get_status(),
    }