import logging
import os
from dataclasses import dataclass
from datetime import timezone
from enum import Enum

from .issue_parser import IssueExtractionError, extract_issue
from .issues_repository import IssueAttachment, IssueRecord, IssuesRepository


class IssueCaptureStatus(str, Enum):
    DISABLED = "disabled"
    INSERTED = "inserted"
    DUPLICATE = "duplicate"
    EXTRACTION_FAILED = "extraction_failed"
    DATABASE_FAILED = "database_failed"
    DELETED = "deleted"


@dataclass(frozen=True)
class IssueCaptureResult:
    status: IssueCaptureStatus
    discord_message_id: str


class IssueCaptureService:
    def __init__(self, repository: IssuesRepository | None, logger: logging.Logger):
        self._repository = repository
        self._logger = logger

    @property
    def enabled(self) -> bool:
        return self._repository is not None

    async def capture_message(self, message: object) -> IssueCaptureResult:
        message_id = str(getattr(message, "id", ""))
        if not self._repository:
            return IssueCaptureResult(IssueCaptureStatus.DISABLED, message_id)

        channel = getattr(message, "channel", None)
        guild = getattr(message, "guild", None)

        self._logger.info(
            "New Discord message received for issue capture",
            extra={
                "discord_message_id": message_id,
                "channel_id": str(getattr(channel, "id", "")),
                "guild_id": str(getattr(guild, "id", "")) if guild else None,
            },
        )

        try:
            created_at = getattr(message, "created_at")
            message_timestamp = created_at.astimezone(timezone.utc)
            message_timestamp_local = created_at.astimezone().replace(tzinfo=None)
            extracted = extract_issue(
                getattr(message, "content", ""),
                getattr(message, "author", None),
                message_timestamp_local,
            )
            self._logger.info(
                "Issue successfully extracted",
                extra={"discord_message_id": message_id},
            )
        except IssueExtractionError:
            self._logger.exception(
                "Extraction failure",
                extra={"discord_message_id": message_id},
            )
            return IssueCaptureResult(IssueCaptureStatus.EXTRACTION_FAILED, message_id)
        except Exception:
            self._logger.exception(
                "Unexpected extraction failure",
                extra={"discord_message_id": message_id},
            )
            return IssueCaptureResult(IssueCaptureStatus.EXTRACTION_FAILED, message_id)

        attachments = self._extract_attachments(message, message_id)

        record = IssueRecord(
            discord_message_id=message_id,
            guild_id=str(guild.id) if guild else None,
            guild_name=getattr(guild, "name", None) if guild else None,
            channel_id=str(getattr(channel, "id", "")),
            channel_name=getattr(channel, "name", None),
            sender=extracted.sender,
            issue_date=extracted.issue_date,
            issue_time=extracted.issue_time,
            issue=extracted.issue,
            message_timestamp=message_timestamp,
            message_timestamp_local=message_timestamp_local,
            attachments=attachments,
        )

        try:
            inserted = await self._repository.insert_issue(record)
        except Exception:
            self._logger.exception(
                "Database failure while inserting issue",
                extra={"discord_message_id": message_id},
            )
            return IssueCaptureResult(IssueCaptureStatus.DATABASE_FAILED, message_id)

        if inserted:
            self._logger.info(
                "Database insert successful",
                extra={
                    "discord_message_id": message_id,
                    "attachment_count": len(attachments),
                },
            )
            return IssueCaptureResult(IssueCaptureStatus.INSERTED, message_id)
        else:
            self._logger.info(
                "Duplicate message detected",
                extra={
                    "discord_message_id": message_id,
                    "attachment_count": len(attachments),
                },
            )
            return IssueCaptureResult(IssueCaptureStatus.DUPLICATE, message_id)

    async def delete_message(self, message_id: str) -> IssueCaptureResult:
        if not self._repository:
            return IssueCaptureResult(IssueCaptureStatus.DISABLED, message_id)

        self._logger.info(
            "Message deletion detected",
            extra={"discord_message_id": message_id},
        )

        try:
            deleted = await self._repository.delete_issue_by_message_id(message_id)
        except Exception:
            self._logger.exception(
                "Database failure while deleting issue",
                extra={"discord_message_id": message_id},
            )
            return IssueCaptureResult(IssueCaptureStatus.DATABASE_FAILED, message_id)

        if deleted:
            self._logger.info(
                "Issue deleted from database",
                extra={"discord_message_id": message_id},
            )
        else:
            self._logger.info(
                "No matching issue found for deletion",
                extra={"discord_message_id": message_id},
            )

        return IssueCaptureResult(IssueCaptureStatus.DELETED, message_id)

    def _extract_attachments(
        self, message: object, message_id: str
    ) -> tuple[IssueAttachment, ...]:
        try:
            raw_attachments = tuple(getattr(message, "attachments", ()) or ())
        except Exception:
            self._logger.exception(
                "Failed to read Discord message attachments",
                extra={"discord_message_id": message_id},
            )
            return ()

        self._logger.info(
            "Discord message attachments detected",
            extra={
                "discord_message_id": message_id,
                "attachment_count": len(raw_attachments),
                "attachment_names": [
                    _safe_attachment_filename(attachment)
                    for attachment in raw_attachments
                ],
            },
        )

        attachments: list[IssueAttachment] = []
        for attachment in raw_attachments:
            try:
                attachments.append(_build_issue_attachment(attachment))
            except Exception:
                self._logger.exception(
                    "Failed to capture Discord attachment metadata",
                    extra={
                        "discord_message_id": message_id,
                        "attachment_id": str(getattr(attachment, "id", "")),
                        "attachment_name": _safe_attachment_filename(attachment),
                    },
                )

        return tuple(attachments)


def _build_issue_attachment(attachment: object) -> IssueAttachment:
    original_file_name = str(getattr(attachment, "filename", "") or "")
    attachment_name, extension = os.path.splitext(original_file_name)
    return IssueAttachment(
        attachment_name=attachment_name,
        original_file_name=original_file_name,
        file_extension=extension[1:].lower() if extension.startswith(".") else extension,
        url=str(getattr(attachment, "url", "") or ""),
        content_type=getattr(attachment, "content_type", None),
        size_bytes=int(getattr(attachment, "size", 0) or 0),
    )


def _safe_attachment_filename(attachment: object) -> str:
    try:
        return str(getattr(attachment, "filename", "") or "")
    except Exception:
        return ""
