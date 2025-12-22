"""
Authentication API Endpoints

Handles user authentication, token management, and password operations.

Security:
- Login attempts are rate limited (5/minute per IP)
- Password changes are strictly rate limited (3/minute per IP)
- IP blocking after 10 failed authentication attempts
- All authentication events are logged to audit_logs
- Failed login attempts are tracked
- Tokens are JWT-based with configurable expiration

Testing Mode:
- Set ENVIRONMENT=testing or TESTING=true for relaxed rate limits
"""

import os
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

# Check if we're in testing mode
_environment = os.getenv("ENVIRONMENT", "development").lower()
_is_testing = os.getenv("TESTING", "false").lower() == "true" or _environment == "testing"

# Rate limit parameters based on environment
_max_login_attempts = 500 if _is_testing else 5

from app.db.session import get_db
from app.dependencies import get_current_active_user, CurrentUser
from app.models.audit_log import AuditAction, AuditStatus
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ChangePasswordRequest,
    MessageResponse,
    UserMeResponse
)
from app.services.auth_service import get_auth_service
from app.services.user_service import get_user_service
from app.core.rate_limiter import limiter, RATE_LIMITS
from app.core.ip_blocker import get_ip_blocker


router = APIRouter()


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="User Login",
    description="Authenticate user with email and password. Returns access and refresh tokens.",
    responses={
        200: {"description": "Successfully authenticated"},
        401: {"description": "Invalid credentials"},
        403: {"description": "IP blocked due to too many failed attempts"},
        429: {"description": "Too many login attempts"}
    }
)
@limiter.limit(RATE_LIMITS["auth_login"])
async def login(
    request: Request,
    response: Response,
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return access and refresh tokens.

    Security:
    - Rate limited to 5 attempts per minute per IP (SlowAPI)
    - IP blocking after 10 failed attempts (1 hour block)
    - Logs all login attempts (success and failure)
    - Returns generic error message for security

    Args:
        request: FastAPI request for context
        credentials: Login credentials (email and password)
        db: Database session

    Returns:
        LoginResponse with user info and tokens

    Raises:
        HTTPException: If credentials are invalid, IP blocked, or rate limit exceeded
    """
    auth_service = get_auth_service(db)
    user_service = get_user_service(db)
    ip_blocker = get_ip_blocker()

    # Get request context for logging
    context = auth_service.get_request_context(request)
    client_ip = context["ip_address"]

    # Check if IP is blocked
    if ip_blocker.is_blocked(client_ip):
        await auth_service.log_auth_event(
            action=AuditAction.LOGIN_FAILED,
            status=AuditStatus.FAILURE,
            ip_address=client_ip,
            user_agent=context["user_agent"],
            error_message="IP blocked due to too many failed attempts",
            details={"email": credentials.email}
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Too many failed attempts. Your IP has been temporarily blocked. Please try again later."
        )

    # Check rate limit per email address
    if not await auth_service.check_login_rate_limit(
        identifier=credentials.email,
        max_attempts=_max_login_attempts,
        window_seconds=300
    ):
        await auth_service.log_auth_event(
            action=AuditAction.LOGIN_FAILED,
            status=AuditStatus.FAILURE,
            ip_address=context["ip_address"],
            user_agent=context["user_agent"],
            error_message="Rate limit exceeded",
            details={"email": credentials.email}
        )

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )

    # Authenticate user
    user = await auth_service.authenticate_user(
        email=credentials.email,
        password=credentials.password
    )

    if not user:
        # Log failed login attempt
        await auth_service.log_auth_event(
            action=AuditAction.LOGIN_FAILED,
            status=AuditStatus.FAILURE,
            ip_address=client_ip,
            user_agent=context["user_agent"],
            error_message="Invalid credentials",
            details={"email": credentials.email}
        )

        # Record failed attempt and check if IP should be blocked
        should_block = ip_blocker.record_failed_attempt(
            client_ip,
            reason="authentication_failed"
        )

        if should_block:
            # IP is now blocked - log it
            await auth_service.log_auth_event(
                action=AuditAction.LOGIN_FAILED,
                status=AuditStatus.FAILURE,
                ip_address=client_ip,
                user_agent=context["user_agent"],
                error_message="IP blocked after repeated failed attempts",
                details={"email": credentials.email}
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Create tokens
    access_token, refresh_token = await auth_service.create_user_tokens(user)

    # Update last login timestamp
    await user_service.update_last_login(user.id)

    # Clear failed attempts on successful login
    ip_blocker.clear_failed_attempts(client_ip)

    # Log successful login
    await auth_service.log_auth_event(
        action=AuditAction.LOGIN,
        status=AuditStatus.SUCCESS,
        user_id=user.id,
        ip_address=client_ip,
        user_agent=context["user_agent"]
    )

    # Convert user to response schema
    user_response = user_service.user_to_response(user)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=user_response
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="User Logout",
    description="Logout user and invalidate current session.",
    responses={
        200: {"description": "Successfully logged out"},
        401: {"description": "Not authenticated"},
        429: {"description": "Too many requests"}
    }
)
@limiter.limit(RATE_LIMITS["read"])  # Lenient rate limit for logout
async def logout(
    request: Request,
    response: Response,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user and invalidate session.

    Note: For stateless JWT, tokens remain valid until expiration.
    This endpoint clears server-side cache and logs the logout event.

    Args:
        request: FastAPI request for context
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message
    """
    auth_service = get_auth_service(db)

    # Get request context for logging
    context = auth_service.get_request_context(request)

    # Logout user (clears cache)
    await auth_service.logout_user(
        user_id=current_user.id,
        token=""  # Token invalidation not implemented for MVP
    )

    # Log logout event
    await auth_service.log_auth_event(
        action=AuditAction.LOGOUT,
        status=AuditStatus.SUCCESS,
        user_id=current_user.id,
        ip_address=context["ip_address"],
        user_agent=context["user_agent"]
    )

    return MessageResponse(message="Successfully logged out")


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Refresh Access Token",
    description="Get a new access token using a valid refresh token.",
    responses={
        200: {"description": "New access token issued"},
        401: {"description": "Invalid or expired refresh token"},
        429: {"description": "Too many requests"}
    }
)
@limiter.limit(RATE_LIMITS["auth_refresh"])  # 10/minute for token refresh
async def refresh_token(
    request: Request,
    response: Response,
    token_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.

    Args:
        token_request: Refresh token request
        db: Database session

    Returns:
        New access token

    Raises:
        HTTPException: If refresh token is invalid
    """
    auth_service = get_auth_service(db)

    # Refresh access token
    access_token = await auth_service.refresh_access_token(
        refresh_token=token_request.refresh_token
    )

    return RefreshTokenResponse(
        access_token=access_token,
        token_type="bearer"
    )


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change Password",
    description="Change current user's password.",
    responses={
        200: {"description": "Password changed successfully"},
        400: {"description": "Invalid current password or password requirements not met"},
        401: {"description": "Not authenticated"},
        429: {"description": "Too many requests"}
    }
)
@limiter.limit(RATE_LIMITS["auth_password"])  # 3/minute - very strict for password operations
async def change_password(
    request: Request,
    response: Response,
    password_data: ChangePasswordRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    Change user password.

    Security:
    - Requires current password verification
    - New password must meet complexity requirements
    - Logs password change event
    - Invalidates user cache

    Args:
        request: FastAPI request for context
        password_data: Current and new passwords
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If current password is invalid
    """
    auth_service = get_auth_service(db)

    # Get request context for logging
    context = auth_service.get_request_context(request)

    try:
        # Change password
        await auth_service.change_user_password(
            user_id=current_user.id,
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )

        # Log password change
        await auth_service.log_auth_event(
            action=AuditAction.PASSWORD_CHANGE,
            status=AuditStatus.SUCCESS,
            user_id=current_user.id,
            ip_address=context["ip_address"],
            user_agent=context["user_agent"]
        )

        return MessageResponse(message="Password changed successfully")

    except HTTPException as e:
        # Log failed password change
        await auth_service.log_auth_event(
            action=AuditAction.PASSWORD_CHANGE,
            status=AuditStatus.FAILURE,
            user_id=current_user.id,
            ip_address=context["ip_address"],
            user_agent=context["user_agent"],
            error_message=str(e.detail)
        )
        raise


@router.get(
    "/me",
    response_model=UserMeResponse,
    summary="Get Current User",
    description="Get current authenticated user information.",
    responses={
        200: {"description": "Current user information"},
        401: {"description": "Not authenticated"},
        429: {"description": "Too many requests"}
    }
)
@limiter.limit(RATE_LIMITS["read"])  # Standard read rate limit
async def get_current_user_info(
    request: Request,
    response: Response,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user information.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Current user information
    """
    user_service = get_user_service(db)

    # Convert user to response schema (decrypts sensitive fields)
    user_response = user_service.user_to_response(current_user)

    return UserMeResponse(user=user_response)
