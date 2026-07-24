"""Pydantic models for MCP tool JSON responses."""

from pydantic import BaseModel


class ReplyMessageResult(BaseModel):
    """Response from the reply_message MCP tool."""

    success: bool
    message_id: str
    reply_to_message_id: str
    channel_id: str
    timestamp: str


class DeleteMessageResult(BaseModel):
    """Response from the moderate_message MCP tool."""

    success: bool
    message_id: str
    channel_id: str
    message_deleted: bool
    timed_out: bool = False
