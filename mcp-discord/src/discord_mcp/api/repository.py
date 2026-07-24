"""Repository for querying and persisting issues via SQLModel."""

import logging
from typing import Optional

from sqlmodel import col, delete, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from .models import IssueRow

logger = logging.getLogger("discord-mcp-api.repository")


class IssueRepository:
    """Repository for reading and writing issues in the database."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_discord_message_id(
        self, discord_message_id: str
    ) -> Optional[IssueRow]:
        """Fetch a single issue by its Discord message ID."""
        result = await self._session.exec(
            select(IssueRow).where(
                IssueRow.discord_message_id == discord_message_id
            )
        )
        return result.first()

    async def get_by_channel_id(self, channel_id: str) -> list[IssueRow]:
        """Fetch all issues for a given channel, newest first."""
        result = await self._session.exec(
            select(IssueRow)
            .where(IssueRow.channel_id == channel_id)
            .order_by(col(IssueRow.created_at).desc())
        )
        return list(result.all())

    async def get_by_sender(
        self, sender: str, skip: int = 0, limit: int = 50
    ) -> tuple[list[IssueRow], int]:
        """Fetch issues by sender with pagination. Returns (rows, total_count)."""
        count_result = await self._session.exec(
            select(func.count()).select_from(IssueRow).where(
                IssueRow.sender == sender
            )
        )
        total = count_result.one()

        result = await self._session.exec(
            select(IssueRow)
            .where(IssueRow.sender == sender)
            .order_by(col(IssueRow.created_at).desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.all()), total

    async def create_issue(self, row: IssueRow) -> IssueRow:
        """Insert a new issue record and return it with generated fields."""
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return row

    async def delete_by_discord_message_id(self, discord_message_id: str) -> bool:
        """Delete the issue matching the given Discord message ID.

        Returns True if a row was deleted, False if no match.
        """
        result = await self._session.exec(
            delete(IssueRow).where(
                IssueRow.discord_message_id == discord_message_id
            )
        )
        await self._session.commit()
        return result.rowcount > 0
