"""Rate limiting middleware."""

import time
from typing import Dict, List, Tuple
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.models.response import ErrorResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter using sliding window algorithm."""

    def __init__(self, requests: int = 10, window: int = 60):
        """
        Initialize rate limiter.

        Args:
            requests: Maximum number of requests allowed
            window: Time window in seconds
        """
        self.max_requests = requests
        self.window = window
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self.cleanup_interval = 300  # Cleanup old entries every 5 minutes
        self.last_cleanup = time.time()

    def _cleanup(self):
        """Remove old entries from memory."""
        current_time = time.time()

        # Only cleanup periodically
        if current_time - self.last_cleanup < self.cleanup_interval:
            return

        # Remove old timestamps
        cutoff = current_time - self.window
        for key in list(self.requests.keys()):
            self.requests[key] = [t for t in self.requests[key] if t > cutoff]

            # Remove empty entries
            if not self.requests[key]:
                del self.requests[key]

        self.last_cleanup = current_time
        logger.debug(f"Rate limiter cleanup: {len(self.requests)} active keys")

    def is_allowed(self, key: str) -> Tuple[bool, int]:
        """
        Check if request is allowed for the given key.

        Args:
            key: Unique identifier (e.g., IP address)

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        current_time = time.time()
        cutoff = current_time - self.window

        # Cleanup periodically
        self._cleanup()

        # Get timestamps within window
        timestamps = self.requests[key]
        timestamps = [t for t in timestamps if t > cutoff]
        self.requests[key] = timestamps

        # Check if under limit
        if len(timestamps) < self.max_requests:
            timestamps.append(current_time)
            return True, 0

        # Calculate retry after
        oldest = min(timestamps)
        retry_after = int(oldest + self.window - current_time) + 1

        return False, retry_after

    def get_usage(self, key: str) -> Dict[str, int]:
        """Get current usage statistics for a key."""
        current_time = time.time()
        cutoff = current_time - self.window

        timestamps = [t for t in self.requests.get(key, []) if t > cutoff]

        return {
            "requests_made": len(timestamps),
            "requests_remaining": max(0, self.max_requests - len(timestamps)),
            "window_seconds": self.window,
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limiting."""

    def __init__(self, app, requests: int = 10, window: int = 60, bypass_paths: List[str] = None):
        """
        Initialize rate limit middleware.

        Args:
            app: FastAPI application
            requests: Maximum requests per window
            window: Time window in seconds
            bypass_paths: List of paths to bypass rate limiting
        """
        super().__init__(app)
        self.limiter = RateLimiter(requests, window)
        self.bypass_paths = bypass_paths or ["/health", "/api/v1/health", "/docs", "/openapi.json"]

    def _get_client_id(self, request: Request) -> str:
        """
        Get client identifier from request.

        Args:
            request: Incoming request

        Returns:
            Client identifier (IP address)
        """
        # Try to get real IP from headers (for proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take first IP in chain
            return forwarded_for.split(",")[0].strip()

        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Check if path should bypass rate limiting
        if request.url.path in self.bypass_paths:
            return await call_next(request)

        # Get client identifier
        client_id = self._get_client_id(request)

        # Check rate limit
        is_allowed, retry_after = self.limiter.is_allowed(client_id)

        if not is_allowed:
            request_id = getattr(request.state, "request_id", None)

            logger.warning(
                f"[{request_id}] Rate limit exceeded for {client_id}: "
                f"{request.method} {request.url.path}"
            )

            # Get usage stats
            usage = self.limiter.get_usage(client_id)

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=ErrorResponse(
                    error="RateLimitExceeded",
                    message=f"Too many requests. Please try again in {retry_after} seconds.",
                    detail={
                        "retry_after": retry_after,
                        "limit": self.limiter.max_requests,
                        "window": self.limiter.window,
                        "usage": usage,
                    },
                    request_id=request_id,
                ).model_dump(),
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.limiter.max_requests),
                    "X-RateLimit-Remaining": str(usage["requests_remaining"]),
                    "X-RateLimit-Reset": str(int(time.time() + retry_after)),
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        usage = self.limiter.get_usage(client_id)
        response.headers["X-RateLimit-Limit"] = str(self.limiter.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(usage["requests_remaining"])
        response.headers["X-RateLimit-Window"] = str(self.limiter.window)

        return response


def create_rate_limit_middleware(app) -> RateLimitMiddleware:
    """
    Create rate limit middleware with settings from config.

    Args:
        app: FastAPI application

    Returns:
        Configured RateLimitMiddleware instance
    """
    settings = get_settings()

    return RateLimitMiddleware(
        app,
        requests=settings.rate_limit_requests,
        window=settings.rate_limit_window,
        bypass_paths=[
            "/",
            "/health",
            "/api/v1/health",
            "/api/v1/status",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
    )