"""
Security Headers Middleware

Adds production-grade security headers to all HTTP responses.

Headers Implemented:
- Strict-Transport-Security (HSTS): Force HTTPS for 1 year
- X-Content-Type-Options: Prevent MIME sniffing
- X-Frame-Options: Prevent clickjacking
- X-XSS-Protection: Enable browser XSS protection (legacy)
- Referrer-Policy: Control referrer information
- Permissions-Policy: Disable unnecessary browser features
- Content-Security-Policy (CSP): Restrict resource loading

Security Benefits:
- Protects against clickjacking attacks
- Prevents MIME-type sniffing vulnerabilities
- Enforces HTTPS connections
- Reduces cross-site scripting (XSS) risks
- Controls which browser features can be used

Production Notes:
- CSP policy should be customized for your frontend domain
- Update connect-src with your actual API domains
- Adjust script-src if using inline scripts (consider using nonces)
- Test thoroughly before deploying to production
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import logging


logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all HTTP responses.

    Implements OWASP recommended security headers for API security.
    """

    def __init__(self, app, enable_csp: bool = True, strict_csp: bool = False):
        """
        Initialize security headers middleware.

        Args:
            app: FastAPI application
            enable_csp: Whether to enable Content Security Policy (default: True)
            strict_csp: Whether to use strict CSP (may break some features)
        """
        super().__init__(app)
        self.enable_csp = enable_csp
        self.strict_csp = strict_csp

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and add security headers to response.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            Response with security headers added
        """
        # Process request through the rest of the application
        response = await call_next(request)

        # Add security headers
        self._add_security_headers(response)

        return response

    def _add_security_headers(self, response: Response) -> None:
        """
        Add all security headers to the response.

        Args:
            response: HTTP response object
        """
        # 1. Strict-Transport-Security (HSTS)
        # Force HTTPS for 1 year, including subdomains
        # Only enable in production with HTTPS configured
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

        # 2. X-Content-Type-Options
        # Prevent MIME-type sniffing
        # Ensures browsers respect the Content-Type header
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 3. X-Frame-Options
        # Prevent clickjacking by disallowing iframe embedding
        # Use DENY to block all framing, or SAMEORIGIN to allow same-origin framing
        response.headers["X-Frame-Options"] = "DENY"

        # 4. X-XSS-Protection
        # Enable browser's XSS filter (legacy header, mostly replaced by CSP)
        # mode=block stops page rendering if XSS is detected
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 5. Referrer-Policy
        # Control how much referrer information is sent with requests
        # strict-origin-when-cross-origin: Send full URL for same-origin,
        # only origin for cross-origin HTTPS, nothing for HTTPS->HTTP
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 6. Permissions-Policy (formerly Feature-Policy)
        # Disable unnecessary browser features to reduce attack surface
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "  # Disable geolocation API
            "microphone=(), "  # Disable microphone access
            "camera=(), "  # Disable camera access
            "payment=(), "  # Disable payment request API
            "usb=(), "  # Disable USB API
            "magnetometer=(), "  # Disable magnetometer
            "gyroscope=(), "  # Disable gyroscope
            "accelerometer=()"  # Disable accelerometer
        )

        # 7. Content-Security-Policy (CSP)
        # Most powerful security header - controls what resources can be loaded
        if self.enable_csp:
            if self.strict_csp:
                # Strict CSP for APIs (no inline scripts/styles)
                csp_policy = (
                    "default-src 'none'; "  # Block everything by default
                    "connect-src 'self'; "  # Allow API calls to same origin only
                    "frame-ancestors 'none'; "  # Prevent framing (redundant with X-Frame-Options)
                    "base-uri 'self'; "  # Restrict <base> tag
                    "form-action 'self';"  # Restrict form submissions
                )
            else:
                # Moderate CSP for API with potential frontend integration
                csp_policy = (
                    "default-src 'self'; "  # Default: same origin only
                    "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # Allow scripts
                    "style-src 'self' 'unsafe-inline'; "  # Allow styles
                    "img-src 'self' data: https:; "  # Allow images from self, data URLs, HTTPS
                    "font-src 'self' data:; "  # Allow fonts
                    "connect-src 'self'; "  # API calls to same origin
                    "frame-ancestors 'none'; "  # No framing
                    "base-uri 'self'; "  # Restrict <base> tag
                    "form-action 'self';"  # Restrict form submissions
                )

            response.headers["Content-Security-Policy"] = csp_policy

        # 8. Additional Security Headers

        # Remove server header to avoid revealing server information
        if "server" in response.headers:
            del response.headers["server"]

        # Remove X-Powered-By if present (usually from proxies)
        if "x-powered-by" in response.headers:
            del response.headers["x-powered-by"]

        # 9. CORS headers are handled by CORSMiddleware
        # Don't override them here

        # Log security headers added (debug only)
        logger.debug(f"Security headers added to response for {response.status_code}")


def create_security_headers_middleware(
    enable_csp: bool = True,
    strict_csp: bool = False
) -> type:
    """
    Factory function to create SecurityHeadersMiddleware with custom config.

    Args:
        enable_csp: Whether to enable Content Security Policy
        strict_csp: Whether to use strict CSP

    Returns:
        SecurityHeadersMiddleware class configured with settings
    """
    class ConfiguredSecurityHeadersMiddleware(SecurityHeadersMiddleware):
        def __init__(self, app):
            super().__init__(app, enable_csp=enable_csp, strict_csp=strict_csp)

    return ConfiguredSecurityHeadersMiddleware
