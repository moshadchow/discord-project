from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any

from psycopg.types.json import Jsonb
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool


@dataclass(frozen=True)
class IssueAttachment:
    attachment_name: str
    original_file_name: str
    file_extension: str
    url: str
    content_type: str | None
    size_bytes: int


@dataclass(frozen=True)
class IssueRecord:
    discord_message_id: str
    guild_id: str | None
    guild_name: str | None
    channel_id: str
    channel_name: str | None
    sender: str
    issue_date: date
    issue_time: time
    issue: str
    message_timestamp: datetime
    message_timestamp_local: datetime
    parent_message_id: str | None = None
    attachments: tuple[IssueAttachment, ...] = ()


class IssuesRepository:
    def __init__(self, database_url: str, *, min_size: int = 1, max_size: int = 5):
        self._pool = AsyncConnectionPool(
            conninfo=database_url,
            min_size=min_size,
            max_size=max_size,
            kwargs={"row_factory": dict_row},
            open=False,
        )

    async def open(self) -> None:
        await self._pool.open()
        await self.ensure_schema()

    async def close(self) -> None:
        await self._pool.close()

    async def ensure_schema(self) -> None:
        async with self._pool.connection() as conn:
            async with conn.transaction():
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS issues (
                        id BIGSERIAL PRIMARY KEY,
                        discord_message_id TEXT UNIQUE NOT NULL,
                        guild_id TEXT,
                        guild_name TEXT,
                        channel_id TEXT NOT NULL,
                        channel_name TEXT,
                        sender TEXT NOT NULL,
                        issue_date DATE NOT NULL,
                        issue_time TIME NOT NULL,
                        issue TEXT NOT NULL,
                        attachments JSONB NOT NULL DEFAULT '[]'::jsonb,
                        message_timestamp TIMESTAMPTZ NOT NULL,
                        message_timestamp_local TIMESTAMP NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    )
                    """
                )
                await conn.execute(
                    """
                    ALTER TABLE issues
                    ADD COLUMN IF NOT EXISTS attachments JSONB NOT NULL DEFAULT '[]'::jsonb
                    """
                )
                await conn.execute(
                    """
                    ALTER TABLE issues
                    ADD COLUMN IF NOT EXISTS parent_message_id TEXT
                    """
                )
                await conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_issues_parent_message_id
                    ON issues(parent_message_id)
                    """
                )

    async def insert_issue(self, issue: IssueRecord) -> bool:
        params: dict[str, Any] = {
            "discord_message_id": issue.discord_message_id,
            "parent_message_id": issue.parent_message_id,
            "guild_id": issue.guild_id,
            "guild_name": issue.guild_name,
            "channel_id": issue.channel_id,
            "channel_name": issue.channel_name,
            "sender": issue.sender,
            "issue_date": issue.issue_date,
            "issue_time": issue.issue_time,
            "issue": issue.issue,
            "attachments": Jsonb(serialize_attachments(issue.attachments)),
            "message_timestamp": issue.message_timestamp,
            "message_timestamp_local": issue.message_timestamp_local,
        }

        async with self._pool.connection() as conn:
            async with conn.transaction():
                cursor = await conn.execute(
                    """
                    INSERT INTO issues (
                        discord_message_id,
                        parent_message_id,
                        guild_id,
                        guild_name,
                        channel_id,
                        channel_name,
                        sender,
                        issue_date,
                        issue_time,
                        issue,
                        attachments,
                        message_timestamp,
                        message_timestamp_local
                    )
                    VALUES (
                        %(discord_message_id)s,
                        %(parent_message_id)s,
                        %(guild_id)s,
                        %(guild_name)s,
                        %(channel_id)s,
                        %(channel_name)s,
                        %(sender)s,
                        %(issue_date)s,
                        %(issue_time)s,
                        %(issue)s,
                        %(attachments)s,
                        %(message_timestamp)s,
                        %(message_timestamp_local)s
                    )
                    ON CONFLICT (discord_message_id) DO NOTHING
                    """,
                    params,
                )
                return cursor.rowcount == 1

    async def delete_issue_by_message_id(self, discord_message_id: str) -> bool:
        async with self._pool.connection() as conn:
            async with conn.transaction():
                cursor = await conn.execute(
                    """
                    DELETE FROM issues
                    WHERE discord_message_id = %(discord_message_id)s
                    """,
                    {"discord_message_id": discord_message_id},
                )
                return cursor.rowcount == 1


def serialize_attachments(
    attachments: tuple[IssueAttachment, ...],
) -> list[dict[str, Any]]:
    return [
        {
            "attachment_name": attachment.attachment_name,
            "original_file_name": attachment.original_file_name,
            "file_extension": attachment.file_extension,
            "url": attachment.url,
            "content_type": attachment.content_type,
            "size_bytes": attachment.size_bytes,
        }
        for attachment in attachments
    ]
