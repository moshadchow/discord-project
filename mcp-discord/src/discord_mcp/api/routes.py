"""API route handlers for issue management and authentication."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from .deps import get_auth_service, get_current_user, get_issue_service
from .schemas import (
    DeleteResponse,
    ErrorResponse,
    IssueListResponse,
    IssueResponse,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    RegisterUserRequest,
    RegisterUserResponse,
    ReplyRequest,
    ReplyResponse,
    UserSummary,
)
from .service import AuthService, IssueQueryService

logger = logging.getLogger("discord-mcp-api.routes")

issue_router = APIRouter(tags=["Messages"])
auth_router = APIRouter(tags=["Auth"])


@issue_router.get(
    "/issues/message/{discord_message_id}",
    response_model=IssueResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_issue_by_message(
    discord_message_id: str,
    service: IssueQueryService = Depends(get_issue_service),
):
    """Fetch a single issue by its Discord message ID."""
    result = await service.get_issue_by_message_id(discord_message_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Issue not found")
    return result


@issue_router.get(
    "/issues/channel/{channel_id}",
    response_model=IssueListResponse,
)
async def get_issues_by_channel(
    channel_id: str,
    service: IssueQueryService = Depends(get_issue_service),
):
    """Fetch all issues for a given Discord channel."""
    rows = await service.get_issues_by_channel_id(channel_id)
    return {"success": True, "count": len(rows), "data": rows}


@issue_router.get(
    "/issues/sender/{sender}",
    response_model=IssueListResponse,
)
async def get_issues_by_sender(
    sender: str,
    skip: int = 0,
    limit: int = 50,
    service: IssueQueryService = Depends(get_issue_service),
):
    """Fetch issues by sender with optional pagination."""
    return await service.get_issues_by_sender(sender, skip, limit)


@issue_router.post(
    "/issues/reply",
    response_model=ReplyResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def reply_to_issue(
    request: ReplyRequest,
    service: IssueQueryService = Depends(get_issue_service),
):
    """Reply to a Discord issue and persist the reply as a new record."""
    try:
        result = await service.reply_to_issue(
            request.discord_message_id, request.message
        )
    except Exception:
        logger.exception("Failed to send Discord reply")
        raise HTTPException(status_code=500, detail="Failed to send Discord message")
    if result is None:
        raise HTTPException(status_code=404, detail="Issue not found")
    return result


@issue_router.delete(
    "/issues/message/{discord_message_id}",
    response_model=DeleteResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def delete_issue_message(
    discord_message_id: str,
    service: IssueQueryService = Depends(get_issue_service),
):
    """Delete the original Discord message and its database record."""
    try:
        result = await service.delete_issue_message(discord_message_id)
    except Exception:
        logger.exception("Failed to delete Discord message")
        raise HTTPException(status_code=500, detail="Failed to delete Discord message")
    if result is None:
        raise HTTPException(status_code=404, detail="Issue not found")
    return result


@auth_router.post(
    "/auth/register",
    response_model=RegisterUserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def register(
    request: RegisterUserRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user account."""
    user_dict, message = await auth_service.register_user(
        username=request.username,
        password=request.password,
        confirm_password=request.confirm_password,
        full_name=request.full_name,
        email=request.email,
        role=request.role or "User",
    )
    if user_dict is None:
        if message == "Passwords do not match.":
            raise HTTPException(status_code=400, detail=message)
        if message in ("Username already exists.", "Email already exists."):
            raise HTTPException(status_code=409, detail=message)
        raise HTTPException(status_code=400, detail=message)
    return RegisterUserResponse(message=message, data=UserSummary(**user_dict))


@auth_router.post(
    "/auth/login",
    response_model=LoginResponse,
    responses={401: {"model": ErrorResponse}},
)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate a user and return a JWT access token."""
    user_dict, token = await auth_service.authenticate_user(
        request.username, request.password
    )
    if user_dict is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )
    from ..config import load_auth_config

    config = load_auth_config()
    return LoginResponse(
        access_token=token,
        expires_in=config.jwt_access_token_expire_minutes * 60,
        user=UserSummary(**user_dict),
    )


@auth_router.post(
    "/auth/logout",
    response_model=LogoutResponse,
)
async def logout():
    """Log out the current user. JWT is stateless; client removes the token."""
    return LogoutResponse(message="Logged out successfully.")


@auth_router.get(
    "/auth/profile",
    response_model=UserSummary,
    responses={401: {"model": ErrorResponse}},
)
async def profile(current_user: dict = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return UserSummary(**current_user)
