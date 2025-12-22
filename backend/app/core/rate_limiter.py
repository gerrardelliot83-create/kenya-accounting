"""
Rate Limiting Configuration

Uses SlowAPI for rate limiting to protect against abuse and DDoS attacks.

Production Note:
- Currently uses in-memory storage (suitable for single-instance deployments)
- For production with multiple instances, use Redis:
  storage_uri="redis://localhost:6379" or storage_uri="redis://redis:6379" (Docker)

Security:
- Rate limits are enforced per IP address
- Different limits for different operation types
- Custom error handler provides user-friendly messages

Testing Mode:
- Set ENVIRONMENT=testing or TESTING=true to use relaxed rate limits
- This allows test suites to run without hitting rate limits
"""

import os
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging


logger = logging.getLogger(__name__)

# Check if we're in testing mode
_environment = os.getenv("ENVIRONMENT", "development").lower()
_is_testing = os.getenv("TESTING", "false").lower() == "true" or _environment == "testing"

if _is_testing:
    logger.info("Rate limiter running in TESTING mode with relaxed limits")


def get_identifier(request: Request) -> str:
    """
    Get identifier for rate limiting.

    Uses IP address as the primary identifier.
    In production, you might want to use authenticated user ID for logged-in users.

    Args:
        request: FastAPI request object

    Returns:
        Identifier string for rate limiting
    """
    # Get client IP
    client_ip = get_remote_address(request)

    # For authenticated endpoints, you could use user ID instead:
    # if hasattr(request.state, "user") and request.state.user:
    #     return f"user:{request.state.user.id}"

    return client_ip


# Configure rate limiter
limiter = Limiter(
    key_func=get_identifier,
    default_limits=["100/minute"],  # Default: 100 requests per minute
    storage_uri="memory://",  # Use Redis in production: "redis://localhost:6379"
    strategy="fixed-window",  # Can also use "moving-window" for more accuracy
    headers_enabled=True,  # Add rate limit info to response headers
)


# Rate limit configurations for different operation types
# Production values - strict limits for security
_PRODUCTION_RATE_LIMITS = {
    # Authentication endpoints (strict limits for security)
    "auth_login": "5/minute",  # Login attempts - prevents brute force
    "auth_password": "3/minute",  # Password changes/resets
    "auth_refresh": "10/minute",  # Token refresh

    # Create operations (moderate)
    "create": "30/minute",  # Creating resources
    "update": "50/minute",  # Updating resources
    "delete": "20/minute",  # Deleting resources

    # Read operations (lenient)
    "read": "100/minute",  # Reading/listing resources
    "read_heavy": "50/minute",  # Heavy read operations (reports, exports)

    # Resource-intensive operations (strict)
    "export_pdf": "10/minute",  # PDF generation
    "export_csv": "15/minute",  # CSV export
    "upload": "5/minute",  # File uploads
    "import": "5/minute",  # Data imports

    # Reconciliation operations (moderate)
    "reconcile": "20/minute",  # Bank reconciliation

    # Reports (moderate)
    "reports": "30/minute",  # Financial reports
}

# Testing values - relaxed limits for running test suites
_TESTING_RATE_LIMITS = {
    "auth_login": "500/minute",
    "auth_password": "100/minute",
    "auth_refresh": "200/minute",
    "create": "500/minute",
    "update": "500/minute",
    "delete": "500/minute",
    "read": "1000/minute",
    "read_heavy": "500/minute",
    "export_pdf": "100/minute",
    "export_csv": "100/minute",
    "upload": "100/minute",
    "import": "100/minute",
    "reconcile": "200/minute",
    "reports": "300/minute",
}

# Use appropriate limits based on environment
RATE_LIMITS = _TESTING_RATE_LIMITS if _is_testing else _PRODUCTION_RATE_LIMITS


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom error handler for rate limit exceeded errors.

    Provides user-friendly error messages and includes retry information.
    Logs rate limit violations for security monitoring.

    Args:
        request: FastAPI request object
        exc: RateLimitExceeded exception

    Returns:
        JSON response with error details
    """
    # Extract retry-after from exception
    retry_after = None
    if hasattr(exc, "detail") and exc.detail:
        # Extract seconds from detail like "1 per 1 minute"
        try:
            # Parse the rate limit detail
            import re
            match = re.search(r"(\d+) per (\d+) (\w+)", exc.detail)
            if match:
                count, period, unit = match.groups()
                period = int(period)

                # Convert to seconds
                if unit == "second" or unit == "seconds":
                    retry_after = period
                elif unit == "minute" or unit == "minutes":
                    retry_after = period * 60
                elif unit == "hour" or unit == "hours":
                    retry_after = period * 3600
        except Exception as e:
            logger.warning(f"Failed to parse rate limit detail: {e}")

    # Log rate limit violation
    client_ip = get_remote_address(request)
    path = request.url.path
    logger.warning(
        f"Rate limit exceeded: {client_ip} - {request.method} {path} - {exc.detail}"
    )

    # Prepare response
    response_content = {
        "error": "RateLimitExceeded",
        "message": "Too many requests. Please try again later.",
        "detail": "You have exceeded the rate limit for this endpoint.",
        "path": path,
    }

    if retry_after:
        response_content["retry_after_seconds"] = retry_after

    return JSONResponse(
        status_code=429,
        content=response_content,
        headers={"Retry-After": str(retry_after) if retry_after else "60"}
    )


def get_rate_limit(operation_type: str) -> str:
    """
    Get rate limit string for a specific operation type.

    Args:
        operation_type: Type of operation (e.g., "auth_login", "create", "export_pdf")

    Returns:
        Rate limit string (e.g., "5/minute")
    """
    return RATE_LIMITS.get(operation_type, "100/minute")


# Decorator factory for easy rate limiting
def rate_limit(limit: str):
    """
    Decorator factory for applying rate limits to endpoints.

    Usage:
        @router.post("/login")
        @rate_limit("5/minute")
        async def login(...):
            ...

    Args:
        limit: Rate limit string (e.g., "5/minute")

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        return limiter.limit(limit)(func)
    return decorator
