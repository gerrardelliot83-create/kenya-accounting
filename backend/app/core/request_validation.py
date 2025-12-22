"""
Request Validation Middleware

Validates incoming HTTP requests for security threats:
- Payload size limits
- Suspicious user agents (security scanners, bots)
- Malformed requests
- Known attack patterns

Security Features:
- Blocks oversized payloads (DDoS protection)
- Detects and blocks common security scanning tools
- Logs suspicious activity for security monitoring
- Returns appropriate HTTP error codes

Production Notes:
- Adjust MAX_CONTENT_LENGTH based on your needs
- Update suspicious_agents list with known threats
- Consider integrating with threat intelligence feeds
- Log blocked requests to SIEM for analysis
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi.responses import JSONResponse
import logging
from typing import List, Optional


logger = logging.getLogger(__name__)


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate incoming requests for security threats.

    Protects against:
    - Payload size attacks (memory exhaustion)
    - Security scanner tools
    - Malicious bots
    - Known attack patterns
    """

    # Maximum allowed content length (10MB default)
    # Adjust based on your file upload requirements
    # For APIs without file uploads, consider 1MB or less
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB

    # Known security scanning and attack tools
    # These user agents are commonly used for vulnerability scanning
    SUSPICIOUS_USER_AGENTS = [
        "sqlmap",  # SQL injection testing
        "nikto",  # Web server scanner
        "nessus",  # Vulnerability scanner
        "openvas",  # Vulnerability scanner
        "nmap",  # Network scanner
        "masscan",  # Port scanner
        "acunetix",  # Web vulnerability scanner
        "burpsuite",  # Security testing
        "metasploit",  # Penetration testing
        "w3af",  # Web application attack framework
        "owasp",  # OWASP testing tools (some legitimate use)
        "dirbuster",  # Directory brute forcing
        "wpscan",  # WordPress scanner
        "havij",  # SQL injection tool
        "wget",  # Command-line downloader (often abused)
        "curl",  # Command-line tool (often abused in automated attacks)
        "python-requests",  # Python library (legitimate but check context)
        "bot",  # Generic bot identifier
        "crawler",  # Generic crawler
        "spider",  # Generic spider
    ]

    # Paths that should allow larger payloads (e.g., file uploads)
    LARGE_PAYLOAD_PATHS = [
        "/api/v1/bank-imports/upload",
        "/api/v1/documents/upload",
        "/api/v1/attachments/upload",
    ]

    def __init__(
        self,
        app,
        max_content_length: Optional[int] = None,
        block_suspicious_agents: bool = True,
        log_suspicious_activity: bool = True
    ):
        """
        Initialize request validation middleware.

        Args:
            app: FastAPI application
            max_content_length: Maximum allowed content length in bytes
            block_suspicious_agents: Whether to block suspicious user agents
            log_suspicious_activity: Whether to log suspicious activity
        """
        super().__init__(app)
        self.max_content_length = max_content_length or self.MAX_CONTENT_LENGTH
        self.block_suspicious_agents = block_suspicious_agents
        self.log_suspicious_activity = log_suspicious_activity

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Validate request and pass to next middleware if valid.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            Response or error if request is invalid
        """
        # 1. Check content length
        validation_result = self._validate_content_length(request)
        if validation_result:
            return validation_result

        # 2. Check user agent
        validation_result = self._validate_user_agent(request)
        if validation_result:
            return validation_result

        # 3. Check for suspicious patterns
        validation_result = self._check_suspicious_patterns(request)
        if validation_result:
            return validation_result

        # All validations passed, proceed
        return await call_next(request)

    def _validate_content_length(self, request: Request) -> Optional[Response]:
        """
        Validate request content length.

        Args:
            request: HTTP request

        Returns:
            Error response if validation fails, None otherwise
        """
        content_length = request.headers.get("content-length")

        if not content_length:
            # No content-length header, skip validation
            # Starlette will handle this
            return None

        try:
            content_length_int = int(content_length)
        except ValueError:
            logger.warning(f"Invalid content-length header: {content_length}")
            return JSONResponse(
                status_code=400,
                content={
                    "error": "BadRequest",
                    "message": "Invalid content-length header"
                }
            )

        # Check if path allows larger payloads
        path = request.url.path
        max_allowed = self.max_content_length

        # Some paths may allow larger uploads
        if any(path.startswith(allowed_path) for allowed_path in self.LARGE_PAYLOAD_PATHS):
            max_allowed = 50 * 1024 * 1024  # 50MB for file uploads
            logger.debug(f"Allowing larger payload for {path}: {max_allowed} bytes")

        if content_length_int > max_allowed:
            client_ip = request.client.host if request.client else "unknown"
            logger.warning(
                f"Payload too large: {content_length_int} bytes from {client_ip} "
                f"to {path} (max: {max_allowed})"
            )

            return JSONResponse(
                status_code=413,
                content={
                    "error": "PayloadTooLarge",
                    "message": f"Request body too large. Maximum allowed: {max_allowed} bytes",
                    "max_size_mb": max_allowed / (1024 * 1024)
                }
            )

        return None

    def _validate_user_agent(self, request: Request) -> Optional[Response]:
        """
        Validate user agent for suspicious patterns.

        Args:
            request: HTTP request

        Returns:
            Error response if validation fails, None otherwise
        """
        if not self.block_suspicious_agents:
            return None

        user_agent = request.headers.get("user-agent", "").lower()

        # Check if user agent is empty (suspicious)
        if not user_agent:
            client_ip = request.client.host if request.client else "unknown"
            logger.warning(f"Request with empty user-agent from {client_ip}")
            # Don't block empty user agents, some legitimate clients don't send them
            # Just log for monitoring
            return None

        # Check against known suspicious agents
        for suspicious_agent in self.SUSPICIOUS_USER_AGENTS:
            if suspicious_agent in user_agent:
                client_ip = request.client.host if request.client else "unknown"
                path = request.url.path

                if self.log_suspicious_activity:
                    logger.warning(
                        f"Suspicious user agent detected: '{user_agent}' "
                        f"from {client_ip} accessing {path}"
                    )

                # For automated security tools, block immediately
                automated_tools = ["sqlmap", "nikto", "nessus", "openvas", "acunetix"]
                if any(tool in user_agent for tool in automated_tools):
                    return JSONResponse(
                        status_code=403,
                        content={
                            "error": "Forbidden",
                            "message": "Access denied"
                        }
                    )

                # For others like curl/wget, log but allow
                # (might be legitimate API usage)
                logger.info(f"Allowing request from potentially suspicious agent: {user_agent}")

        return None

    def _check_suspicious_patterns(self, request: Request) -> Optional[Response]:
        """
        Check for suspicious patterns in request.

        Args:
            request: HTTP request

        Returns:
            Error response if validation fails, None otherwise
        """
        path = request.url.path

        # Check for common attack patterns in path
        suspicious_patterns = [
            "../",  # Path traversal
            "..\\",  # Path traversal (Windows)
            "<script",  # XSS attempt
            "javascript:",  # XSS attempt
            "eval(",  # Code injection
            "exec(",  # Code injection
            "system(",  # Command injection
            "phpinfo",  # PHP info disclosure
            ".env",  # Environment file access
            "/etc/passwd",  # Linux password file
            "wp-admin",  # WordPress admin (if not WP site)
            "wp-login",  # WordPress login
            "phpmyadmin",  # phpMyAdmin (common target)
        ]

        path_lower = path.lower()
        for pattern in suspicious_patterns:
            if pattern in path_lower:
                client_ip = request.client.host if request.client else "unknown"

                if self.log_suspicious_activity:
                    logger.warning(
                        f"Suspicious pattern '{pattern}' detected in path: {path} "
                        f"from {client_ip}"
                    )

                # Don't block immediately, might be false positive
                # Just log for monitoring
                # In production, consider blocking known attack paths

        # Check query parameters for SQL injection patterns
        query_params = str(request.url.query)
        sql_patterns = [
            "union select",
            "union all select",
            "' or '1'='1",
            "' or 1=1",
            "'; drop table",
            "'; delete from",
        ]

        query_lower = query_params.lower()
        for pattern in sql_patterns:
            if pattern in query_lower:
                client_ip = request.client.host if request.client else "unknown"

                logger.error(
                    f"SQL injection attempt detected from {client_ip}: {query_params}"
                )

                # Block SQL injection attempts immediately
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "BadRequest",
                        "message": "Invalid request parameters"
                    }
                )

        return None
