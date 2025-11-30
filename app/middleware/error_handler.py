"""Global error handling middleware."""

import time
import traceback
from uuid import uuid4
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.models.response import ErrorResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware to handle all exceptions and return structured error responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle any exceptions."""
        # Generate request ID if not present
        request_id = getattr(request.state, "request_id", None) or str(uuid4())
        request.state.request_id = request_id

        # Add request ID to headers for tracing
        start_time = time.time()

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
            return response

        except Exception as exc:
            # Log the error with request context
            duration = time.time() - start_time
            logger.error(
                f"[{request_id}] Unhandled exception after {duration:.2f}s: "
                f"{request.method} {request.url.path}",
                exc_info=True
            )

            # Return structured error response
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=ErrorResponse(
                    error="InternalServerError",
                    message="An unexpected error occurred",
                    detail=str(exc) if logger.level <= 10 else None,  # Only in DEBUG
                    request_id=request_id,
                ).model_dump(),
                headers={
                    "X-Request-ID": request_id,
                    "X-Response-Time": f"{duration * 1000:.2f}ms",
                }
            )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle validation errors from Pydantic models.

    Args:
        request: The incoming request
        exc: The validation exception

    Returns:
        JSONResponse with structured error details
    """
    request_id = getattr(request.state, "request_id", None) or str(uuid4())

    # Extract validation errors
    errors = {}
    for error in exc.errors():
        field_path = ".".join(str(loc) for loc in error["loc"])
        if field_path not in errors:
            errors[field_path] = []
        errors[field_path].append(error["msg"])

    logger.warning(
        f"[{request_id}] Validation error: {request.method} {request.url.path} - {errors}"
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="ValidationError",
            message="Request validation failed",
            detail=errors,
            request_id=request_id,
        ).model_dump(),
        headers={"X-Request-ID": request_id}
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions.

    Args:
        request: The incoming request
        exc: The HTTP exception

    Returns:
        JSONResponse with structured error details
    """
    request_id = getattr(request.state, "request_id", None) or str(uuid4())

    logger.warning(
        f"[{request_id}] HTTP exception: {request.method} {request.url.path} - "
        f"{exc.status_code} {exc.detail}"
    )

    # Map status codes to error types
    error_map = {
        400: "BadRequest",
        401: "Unauthorized",
        403: "Forbidden",
        404: "NotFound",
        405: "MethodNotAllowed",
        408: "RequestTimeout",
        429: "RateLimitExceeded",
        500: "InternalServerError",
        502: "BadGateway",
        503: "ServiceUnavailable",
        504: "GatewayTimeout",
    }

    error_type = error_map.get(exc.status_code, "HttpError")

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=error_type,
            message=str(exc.detail) if exc.detail else "An error occurred",
            detail=exc.detail if isinstance(exc.detail, dict) else None,
            request_id=request_id,
        ).model_dump(),
        headers={"X-Request-ID": request_id}
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle general Python exceptions.

    Args:
        request: The incoming request
        exc: The exception

    Returns:
        JSONResponse with structured error details
    """
    request_id = getattr(request.state, "request_id", None) or str(uuid4())

    # Log full traceback
    logger.error(
        f"[{request_id}] Unhandled exception: {request.method} {request.url.path}",
        exc_info=exc
    )

    # Determine if we should expose details
    from app.config import get_settings
    settings = get_settings()
    expose_errors = settings.is_development or settings.log_level == "DEBUG"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc() if expose_errors else None,
            } if expose_errors else None,
            request_id=request_id,
        ).model_dump(),
        headers={"X-Request-ID": request_id}
    )