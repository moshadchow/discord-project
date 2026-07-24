"""API route handlers for issue management."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from .deps import get_issue_service
from .schemas import (
    DeleteResponse,
    ErrorResponse,
    IssueListResponse,
    IssueResponse,
    ReplyRequest,
    ReplyResponse,
)
from .service import IssueQueryService

logger = logging.getLogger("discord-mcp-api.routes")

router = APIRouter()


@router.get(
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


@router.get(
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


@router.get(
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


@router.post(
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


@router.delete(
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
