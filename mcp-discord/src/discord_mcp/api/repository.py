"""Repository for querying and persisting issues and users via SQLModel."""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import col, delete, func, select, text
from sqlmodel.ext.asyncio.session import AsyncSession

from .models import IssueRow, UserRow

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


class UserRepository:
    """Repository for reading and writing users in the database."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def ensure_users_table(self) -> None:
        """Create the users table if it does not exist."""
        await self._session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name VARCHAR(200) NOT NULL,
                    email VARCHAR(255) UNIQUE,
                    role VARCHAR(50) NOT NULL DEFAULT 'User',
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    last_login_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
        )
        await self._session.commit()

    async def get_by_username(self, username: str) -> Optional[UserRow]:
        """Fetch a single user by username."""
        result = await self._session.exec(
            select(UserRow).where(UserRow.username == username)
        )
        return result.first()

    async def get_by_email(self, email: str) -> Optional[UserRow]:
        """Fetch a single user by email."""
        result = await self._session.exec(
            select(UserRow).where(UserRow.email == email)
        )
        return result.first()

    async def get_by_id(self, user_id: int) -> Optional[UserRow]:
        """Fetch a single user by ID."""
        result = await self._session.exec(
            select(UserRow).where(UserRow.id == user_id)
        )
        return result.first()

    async def create_user(self, row: UserRow) -> UserRow:
        """Insert a new user record and return it with generated fields."""
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return row

    async def update_last_login(self, user_id: int) -> None:
        """Update the last_login_at timestamp for a user."""
        result = await self._session.exec(
            select(UserRow).where(UserRow.id == user_id)
        )
        user = result.first()
        if user is not None:
            user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
            user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            self._session.add(user)
            await self._session.commit()
