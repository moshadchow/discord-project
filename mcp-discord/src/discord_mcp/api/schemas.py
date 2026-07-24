"""Pydantic request/response schemas for the API."""

from datetime import date, datetime, time
from typing import Any, Optional

from pydantic import BaseModel


class IssueAttachmentResponse(BaseModel):
    """Attachment metadata in API responses."""

    attachment_name: str
    original_file_name: str
    file_extension: str
    url: str
    content_type: Optional[str] = None
    size_bytes: int


class IssueResponse(BaseModel):
    """Single issue in API responses."""

    discord_message_id: str
    parent_message_id: Optional[str] = None
    guild_id: Optional[str] = None
    guild_name: Optional[str] = None
    channel_id: str
    channel_name: Optional[str] = None
    sender: str
    issue_date: date
    issue_time: time
    issue: str
    attachments: list[IssueAttachmentResponse]
    message_timestamp: datetime
    message_timestamp_local: datetime
    created_at: datetime
    updated_at: datetime


class IssueListResponse(BaseModel):
    """Paginated list of issues."""

    success: bool = True
    count: int
    data: list[IssueResponse]


class ReplyRequest(BaseModel):
    """Request body for sending a reply to a Discord issue."""

    discord_message_id: str
    message: str


class ReplyResponse(BaseModel):
    """Response after sending a Discord reply and persisting it."""

    success: bool = True
    message_sent: bool
    data: dict[str, Any]


class DeleteResponse(BaseModel):
    """Response after deleting a Discord message and its database record."""

    success: bool = True
    discord_message_id: str
    channel_id: str
    message_deleted: bool
    database_record_deleted: bool


class ErrorResponse(BaseModel):
    """Standard error response."""

    success: bool = False
    message: str
