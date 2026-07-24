"""Service layer for issue query and mutation business logic, and authentication."""

import logging
from datetime import datetime, timezone
from typing import Optional

from .discord_gateway import DiscordGateway
from .models import IssueRow, UserRow
from .repository import IssueRepository, UserRepository
from ..core.security import verify_password

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


class AuthService:
    """Business logic for user authentication."""

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def authenticate_user(
        self, username: str, password: str
    ) -> tuple[Optional[dict], Optional[str]]:
        """Authenticate a user by username and password.

        Returns (user_dict, token) on success, or (None, error_message) on failure.
        """
        logger.info("Login attempt", extra={"username": username})

        user = await self._repository.get_by_username(username)
        if user is None:
            logger.warning("Failed login: user not found", extra={"username": username})
            return None, "Invalid username or password."

        if not verify_password(password, user.password_hash):
            logger.warning("Failed login: wrong password", extra={"username": username})
            return None, "Invalid username or password."

        if not user.is_active:
            logger.warning("Failed login: inactive user", extra={"username": username})
            return None, "Invalid username or password."

        await self._repository.update_last_login(user.id)

        from ..core.jwt import create_access_token

        token = create_access_token(user.id, user.username, user.role)

        logger.info("Successful login", extra={"username": username, "user_id": user.id})

        return _user_to_dict(user), token

    async def get_current_user_from_token(self, token: str) -> Optional[dict]:
        """Validate a JWT token and return the corresponding user dict.

        Returns None if the token is invalid, expired, or the user is not found.
        """
        try:
            from ..core.jwt import decode_access_token

            payload = decode_access_token(token)
        except Exception:
            logger.warning("JWT validation failed")
            return None

        user_id_str = payload.get("sub")
        if user_id_str is None:
            return None

        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            return None

        user = await self._repository.get_by_id(user_id)
        if user is None or not user.is_active:
            return None

        return _user_to_dict(user)

    async def register_user(
        self,
        username: str,
        password: str,
        confirm_password: str,
        full_name: str,
        email: str | None = None,
        role: str = "User",
    ) -> tuple[Optional[dict], Optional[str]]:
        """Register a new user.

        Returns (user_dict, success_message) on success,
        or (None, error_message) on failure.
        """
        logger.info("Registration attempt", extra={"username": username})

        if password != confirm_password:
            logger.warning("Registration failed: password mismatch", extra={"username": username})
            return None, "Passwords do not match."

        existing = await self._repository.get_by_username(username)
        if existing is not None:
            logger.warning("Registration failed: duplicate username", extra={"username": username})
            return None, "Username already exists."

        if email is not None:
            existing_email = await self._repository.get_by_email(email)
            if existing_email is not None:
                logger.warning("Registration failed: duplicate email", extra={"username": username})
                return None, "Email already exists."

        from ..core.security import hash_password

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        user_row = UserRow(
            username=username,
            password_hash=hash_password(password),
            full_name=full_name,
            email=email,
            role=role,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        try:
            created = await self._repository.create_user(user_row)
        except Exception:
            logger.exception("Failed to create user", extra={"username": username})
            raise

        logger.info("User registered", extra={"username": username, "user_id": created.id})

        return _user_to_dict(created), "User registered successfully."


def _user_to_dict(row: UserRow) -> dict:
    """Convert a UserRow to a dictionary suitable for API responses."""
    return {
        "id": row.id,
        "username": row.username,
        "full_name": row.full_name,
        "role": row.role,
    }
