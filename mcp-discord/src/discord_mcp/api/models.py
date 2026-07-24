"""SQLModel table mapping for the existing issues table."""

from datetime import date, datetime, time
from typing import Any, Optional

from sqlalchemy import JSON
from sqlmodel import Field, SQLModel


class IssueRow(SQLModel, table=True):
    """Maps to the existing PostgreSQL issues table."""

    __tablename__ = "issues"

    id: Optional[int] = Field(default=None, primary_key=True)
    discord_message_id: str = Field(unique=True, index=True)
    parent_message_id: Optional[str] = Field(default=None, index=True)
    guild_id: Optional[str] = None
    guild_name: Optional[str] = None
    channel_id: str = Field(index=True)
    channel_name: Optional[str] = None
    sender: str = Field(index=True)
    issue_date: date
    issue_time: time
    issue: str
    attachments: Any = Field(sa_type=JSON, default=list)
    message_timestamp: datetime
    message_timestamp_local: datetime
    created_at: datetime
    updated_at: datetime
