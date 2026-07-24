"""Service layer for issue query and mutation business logic."""

import logging
from datetime import datetime, timezone
from typing import Optional

from .discord_gateway import DiscordGateway
from .models import IssueRow
from .repository import IssueRepository

logger = logging.getLogger("discord-mcp-api.service")


class IssueQueryService:
    """Business logic for querying and mutating issues."""

    def __init__(self, repository: IssueRepository, gateway: DiscordGateway) -> None:
        self._repository = repository
        self._gateway = gateway

    async def get_issue_by_message_id(
        self, discord_message_id: str
    ) -> Optional[dict]:
        """Get a single issue by Discord message ID, or None if not found."""
        row = await self._repository.get_by_discord_message_id(discord_message_id)
        if row is None:
            return None
        return _row_to_dict(row)

    async def get_issues_by_channel_id(self, channel_id: str) -> list[dict]:
        """Get all issues for a channel."""
        rows = await self._repository.get_by_channel_id(channel_id)
        return [_row_to_dict(r) for r in rows]

    async def get_issues_by_sender(
        self, sender: str, skip: int = 0, limit: int = 50
    ) -> dict:
        """Get paginated issues by sender with total count."""
        rows, total = await self._repository.get_by_sender(sender, skip, limit)
        return {
            "success": True,
            "count": total,
            "data": [_row_to_dict(r) for r in rows],
        }

    async def reply_to_issue(
        self, discord_message_id: str, message: str
    ) -> Optional[dict]:
        """Reply to an existing issue and persist the reply as a new record.

        Returns None if the original issue is not found.
        Raises on Discord or database failures.
        """
        original = await self._repository.get_by_discord_message_id(discord_message_id)
        if original is None:
            return None

        logger.info(
            "Replying to issue",
            extra={
                "discord_message_id": discord_message_id,
                "channel_id": original.channel_id,
            },
        )

        reply_result = await self._gateway.reply_message(
            channel_id=original.channel_id,
            discord_message_id=discord_message_id,
            message=message,
        )

        logger.info(
            "Discord reply sent",
            extra={
                "channel_id": original.channel_id,
                "new_discord_message_id": reply_result.message_id,
            },
        )

        now_utc = datetime.now(timezone.utc)
        now_naive = now_utc.replace(tzinfo=None)
        now_local = now_utc.astimezone().replace(tzinfo=None)

        new_row = IssueRow(
            discord_message_id=reply_result.message_id,
            parent_message_id=original.discord_message_id,
            guild_id=original.guild_id,
            guild_name=original.guild_name,
            channel_id=original.channel_id,
            channel_name=original.channel_name,
            sender="BOT",
            issue_date=now_local.date(),
            issue_time=now_local.time().replace(tzinfo=None),
            issue=message,
            attachments=[],
            message_timestamp=now_naive,
            message_timestamp_local=now_local,
            created_at=now_naive,
            updated_at=now_naive,
        )

        try:
            inserted = await self._repository.create_issue(new_row)
        except Exception:
            logger.exception(
                "Failed to persist reply to database",
                extra={
                    "new_discord_message_id": reply_result.message_id,
                    "channel_id": original.channel_id,
                },
            )
            raise

        logger.info(
            "Reply persisted to database",
            extra={"new_discord_message_id": reply_result.message_id},
        )

        return {
            "success": True,
            "message_sent": True,
            "data": {
                "id": inserted.id,
                "discord_message_id": inserted.discord_message_id,
                "parent_message_id": inserted.parent_message_id,
                "channel_id": inserted.channel_id,
                "sender": inserted.sender,
                "issue": inserted.issue,
                "message_timestamp": inserted.message_timestamp.isoformat(),
            },
        }

    async def delete_issue_message(
        self, discord_message_id: str
    ) -> Optional[dict]:
        """Delete a Discord message and its database record.

        Returns None if the issue is not found.
        Raises on Discord API failures.
        """
        row = await self._repository.get_by_discord_message_id(discord_message_id)
        if row is None:
            return None

        channel_id = row.channel_id
        logger.info(
            "Deleting Discord issue message",
            extra={
                "discord_message_id": discord_message_id,
                "channel_id": channel_id,
            },
        )

        try:
            await self._gateway.delete_message(
                channel_id=channel_id,
                message_id=discord_message_id,
            )
        except Exception:
            logger.exception(
                "Failed to delete Discord message",
                extra={
                    "discord_message_id": discord_message_id,
                    "channel_id": channel_id,
                },
            )
            raise

        logger.info(
            "Discord message deleted",
            extra={
                "discord_message_id": discord_message_id,
                "channel_id": channel_id,
            },
        )

        db_deleted = False
        try:
            db_deleted = await self._repository.delete_by_discord_message_id(
                discord_message_id
            )
        except Exception:
            logger.exception(
                "Discord message deleted but failed to remove database record",
                extra={
                    "discord_message_id": discord_message_id,
                    "channel_id": channel_id,
                },
            )

        if db_deleted:
            logger.info(
                "Database record deleted",
                extra={"discord_message_id": discord_message_id},
            )

        return {
            "success": True,
            "discord_message_id": discord_message_id,
            "channel_id": channel_id,
            "message_deleted": True,
            "database_record_deleted": db_deleted,
        }


def _row_to_dict(row: IssueRow) -> dict:
    """Convert an IssueRow to a dictionary suitable for API responses."""
    attachments = row.attachments if isinstance(row.attachments, list) else []
    return {
        "discord_message_id": row.discord_message_id,
        "parent_message_id": row.parent_message_id,
        "guild_id": row.guild_id,
        "guild_name": row.guild_name,
        "channel_id": row.channel_id,
        "channel_name": row.channel_name,
        "sender": row.sender,
        "issue_date": row.issue_date,
        "issue_time": row.issue_time,
        "issue": row.issue,
        "attachments": attachments,
        "message_timestamp": row.message_timestamp,
        "message_timestamp_local": row.message_timestamp_local,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }
