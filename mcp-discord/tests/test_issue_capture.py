import logging
import unittest
from datetime import datetime, time, timezone
from types import SimpleNamespace

from discord_mcp.issue_capture import IssueCaptureService, IssueCaptureStatus


class FakeRepository:
    def __init__(self, inserted, error=None, deleted=True):
        self.inserted = inserted
        self.error = error
        self.deleted = deleted
        self.records = []
        self.deleted_ids = []

    async def insert_issue(self, record):
        if self.error:
            raise self.error
        self.records.append(record)
        return self.inserted

    async def delete_issue_by_message_id(self, discord_message_id: str) -> bool:
        if self.error:
            raise self.error
        self.deleted_ids.append(discord_message_id)
        return self.deleted


class IssueCaptureServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_empty_message_is_skipped(self):
        repository = FakeRepository(inserted=True)
        service = IssueCaptureService(repository, _silent_logger("test-empty-message"))
        message = _message(content="  ")

        result = await service.capture_message(message)

        self.assertEqual(repository.records, [])
        self.assertEqual(result.status, IssueCaptureStatus.EXTRACTION_FAILED)

    async def test_duplicate_insert_is_not_error(self):
        repository = FakeRepository(inserted=False)
        service = IssueCaptureService(repository, _silent_logger("test-duplicate-message"))
        message = _message(
            content="Issue at 12:45",
            attachments=[_attachment("error.log", "text/plain", 512)],
        )

        result = await service.capture_message(message)

        self.assertEqual(len(repository.records), 1)
        self.assertEqual(repository.records[0].discord_message_id, "123")
        self.assertEqual(repository.records[0].attachments[0].original_file_name, "error.log")
        self.assertEqual(result.status, IssueCaptureStatus.DUPLICATE)

    async def test_inserted_record_contains_expected_metadata(self):
        repository = FakeRepository(inserted=True)
        service = IssueCaptureService(repository, _silent_logger("test-insert-message"))
        message = _message(content="Database connection failures")

        result = await service.capture_message(message)

        record = repository.records[0]
        self.assertEqual(record.guild_id, "789")
        self.assertEqual(record.guild_name, "Support")
        self.assertEqual(record.channel_id, "456")
        self.assertEqual(record.channel_name, "issues")
        self.assertEqual(record.sender, "Ada")
        self.assertEqual(record.attachments, ())
        self.assertEqual(result.status, IssueCaptureStatus.INSERTED)

    async def test_inserted_record_contains_single_attachment_metadata(self):
        repository = FakeRepository(inserted=True)
        service = IssueCaptureService(repository, _silent_logger("test-single-attachment"))
        message = _message(
            content="Database connection failures",
            attachments=[
                _attachment(
                    "screenshot.PNG",
                    "image/png",
                    2048,
                    url="https://cdn.discordapp.com/attachments/1/screenshot.PNG",
                )
            ],
        )

        result = await service.capture_message(message)

        attachment = repository.records[0].attachments[0]
        self.assertEqual(attachment.attachment_name, "screenshot")
        self.assertEqual(attachment.original_file_name, "screenshot.PNG")
        self.assertEqual(attachment.file_extension, "png")
        self.assertEqual(
            attachment.url,
            "https://cdn.discordapp.com/attachments/1/screenshot.PNG",
        )
        self.assertEqual(attachment.content_type, "image/png")
        self.assertEqual(attachment.size_bytes, 2048)
        self.assertEqual(result.status, IssueCaptureStatus.INSERTED)

    async def test_inserted_record_contains_multiple_attachment_types(self):
        repository = FakeRepository(inserted=True)
        service = IssueCaptureService(repository, _silent_logger("test-multiple-attachments"))
        message = _message(
            content="Database connection failures",
            attachments=[
                _attachment("report.pdf", "application/pdf", 4096),
                _attachment("trace.log", "text/plain", 1024),
                _attachment("archive.zip", None, 8192),
            ],
        )

        result = await service.capture_message(message)

        attachments = repository.records[0].attachments
        self.assertEqual(
            [attachment.original_file_name for attachment in attachments],
            ["report.pdf", "trace.log", "archive.zip"],
        )
        self.assertEqual(
            [attachment.file_extension for attachment in attachments],
            ["pdf", "log", "zip"],
        )
        self.assertIsNone(attachments[2].content_type)
        self.assertEqual(result.status, IssueCaptureStatus.INSERTED)

    async def test_attachment_metadata_error_does_not_block_issue_insert(self):
        repository = FakeRepository(inserted=True)
        service = IssueCaptureService(repository, _silent_logger("test-attachment-error"))
        message = _message(
            content="Database connection failures",
            attachments=[
                _attachment("good.txt", "text/plain", 32),
                BrokenAttachment(),
            ],
        )

        result = await service.capture_message(message)

        attachments = repository.records[0].attachments
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0].original_file_name, "good.txt")
        self.assertEqual(result.status, IssueCaptureStatus.INSERTED)

    async def test_issue_time_preserves_original_message_wall_clock_time(self):
        repository = FakeRepository(inserted=True)
        service = IssueCaptureService(repository, _silent_logger("test-message-time"))
        message = _message(
            content="Database connection failures",
            created_at=datetime(
                2026,
                7,
                12,
                6,
                33,
                45,
                220000,
                tzinfo=timezone.utc,
            ),
        )

        result = await service.capture_message(message)

        record = repository.records[0]
        self.assertEqual(record.issue_time, time(12, 33, 45, 220000))
        self.assertEqual(
            record.message_timestamp,
            datetime(2026, 7, 12, 6, 33, 45, 220000, tzinfo=timezone.utc),
        )
        self.assertEqual(result.status, IssueCaptureStatus.INSERTED)

    async def test_database_error_is_reported(self):
        repository = FakeRepository(inserted=False, error=RuntimeError("db down"))
        service = IssueCaptureService(repository, _silent_logger("test-db-error"))
        message = _message(content="Database connection failures")

        result = await service.capture_message(message)

        self.assertEqual(result.status, IssueCaptureStatus.DATABASE_FAILED)

    async def test_disabled_capture_is_reported(self):
        service = IssueCaptureService(None, _silent_logger("test-disabled"))
        message = _message(content="Database connection failures")

        result = await service.capture_message(message)

        self.assertEqual(result.status, IssueCaptureStatus.DISABLED)


class IssueDeletionServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_delete_removes_matching_issue(self):
        repository = FakeRepository(inserted=True, deleted=True)
        service = IssueCaptureService(repository, _silent_logger("test-delete"))

        result = await service.delete_message("123")

        self.assertEqual(result.status, IssueCaptureStatus.DELETED)
        self.assertEqual(repository.deleted_ids, ["123"])

    async def test_delete_no_matching_issue(self):
        repository = FakeRepository(inserted=True, deleted=False)
        service = IssueCaptureService(repository, _silent_logger("test-delete-no-match"))

        result = await service.delete_message("999")

        self.assertEqual(result.status, IssueCaptureStatus.DELETED)
        self.assertEqual(repository.deleted_ids, ["999"])

    async def test_delete_database_error(self):
        repository = FakeRepository(inserted=True, error=RuntimeError("db down"))
        service = IssueCaptureService(repository, _silent_logger("test-delete-db-error"))

        result = await service.delete_message("456")

        self.assertEqual(result.status, IssueCaptureStatus.DATABASE_FAILED)

    async def test_delete_disabled_capture(self):
        service = IssueCaptureService(None, _silent_logger("test-delete-disabled"))

        result = await service.delete_message("789")

        self.assertEqual(result.status, IssueCaptureStatus.DISABLED)


def _message(content, created_at=None, attachments=None):
    return SimpleNamespace(
        id=123,
        content=content,
        created_at=created_at
        or datetime(2026, 7, 12, 10, 30, tzinfo=timezone.utc),
        author=SimpleNamespace(display_name="Ada", name="ada-user"),
        channel=SimpleNamespace(id=456, name="issues"),
        guild=SimpleNamespace(id=789, name="Support"),
        attachments=attachments or [],
    )


def _attachment(filename, content_type, size, url=None):
    return SimpleNamespace(
        id=f"attachment-{filename}",
        filename=filename,
        content_type=content_type,
        size=size,
        url=url or f"https://cdn.discordapp.com/attachments/1/{filename}",
    )


class BrokenAttachment:
    id = "broken"
    filename = "broken.bin"
    url = "https://cdn.discordapp.com/attachments/1/broken.bin"
    content_type = "application/octet-stream"

    @property
    def size(self):
        raise RuntimeError("metadata unavailable")


def _silent_logger(name):
    logger = logging.getLogger(name)
    logger.disabled = True
    return logger
