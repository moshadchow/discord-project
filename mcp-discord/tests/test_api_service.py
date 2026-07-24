"""Unit tests for the issue query service."""

import json
import unittest
from datetime import date, datetime, time
from unittest.mock import AsyncMock

from discord_mcp.api.mcp_models import DeleteMessageResult, ReplyMessageResult


class FakeIssueRow:
    """Minimal IssueRow stand-in for service tests."""

    def __init__(self, **kwargs):
        defaults = {
            "id": 1,
            "discord_message_id": "100",
            "parent_message_id": None,
            "guild_id": "g1",
            "guild_name": "Test Guild",
            "channel_id": "123456789",
            "channel_name": "general",
            "sender": "alice",
            "issue_date": date(2024, 6, 15),
            "issue_time": time(10, 30),
            "issue": "Login button not working",
            "attachments": json.dumps([]),
            "message_timestamp": datetime(2024, 6, 15, 10, 30),
            "message_timestamp_local": datetime(2024, 6, 15, 12, 30),
            "created_at": datetime(2024, 6, 15, 10, 30),
            "updated_at": datetime(2024, 6, 15, 10, 30),
        }
        defaults.update(kwargs)
        for k, v in defaults.items():
            setattr(self, k, v)


class FakeRepository:
    """In-memory repository for service tests."""

    def __init__(self, rows=None):
        self._rows = list(rows or [])
        self._next_id = max((r.id for r in self._rows), default=0) + 1

    async def get_by_discord_message_id(self, msg_id):
        for r in self._rows:
            if r.discord_message_id == msg_id:
                return r
        return None

    async def get_by_channel_id(self, channel_id):
        return [r for r in self._rows if r.channel_id == channel_id]

    async def get_by_sender(self, sender, skip=0, limit=50):
        matching = [r for r in self._rows if r.sender == sender]
        return matching[skip : skip + limit], len(matching)

    async def create_issue(self, row):
        row.id = self._next_id
        self._next_id += 1
        self._rows.append(row)
        return row

    async def delete_by_discord_message_id(self, msg_id):
        for i, r in enumerate(self._rows):
            if r.discord_message_id == msg_id:
                self._rows.pop(i)
                return True
        return False


class FakeGateway:
    """In-memory gateway for service tests."""

    def __init__(self, reply_result=None, delete_result=None):
        self._reply_result = reply_result or ReplyMessageResult(
            success=True,
            message_id="999",
            reply_to_message_id="123",
            channel_id="987654321",
            timestamp="2026-07-24T10:15:30+00:00",
        )
        self._delete_result = delete_result or DeleteMessageResult(
            success=True,
            message_id="123",
            channel_id="987654321",
            message_deleted=True,
        )

    async def reply_message(self, channel_id, discord_message_id, message):
        return self._reply_result

    async def delete_message(self, channel_id, message_id, reason="Deleted via API"):
        return self._delete_result


class IssueQueryServiceTests(unittest.IsolatedAsyncioTestCase):
    """Tests for IssueQueryService business logic."""

    def _make_service(self, rows=None, gateway=None):
        from discord_mcp.api.service import IssueQueryService

        return IssueQueryService(FakeRepository(rows), gateway or FakeGateway())

    async def test_get_issue_by_message_id_returns_none(self):
        service = self._make_service()
        result = await service.get_issue_by_message_id("nonexistent")
        self.assertIsNone(result)

    async def test_get_issue_by_message_id_returns_dict(self):
        row = FakeIssueRow(discord_message_id="123")
        service = self._make_service([row])
        result = await service.get_issue_by_message_id("123")
        self.assertIsNotNone(result)
        self.assertEqual(result["discord_message_id"], "123")
        self.assertEqual(result["sender"], "alice")

    async def test_get_issues_by_channel_id(self):
        rows = [
            FakeIssueRow(channel_id="ch1", discord_message_id="1"),
            FakeIssueRow(channel_id="ch1", discord_message_id="2"),
            FakeIssueRow(channel_id="ch2", discord_message_id="3"),
        ]
        service = self._make_service(rows)
        result = await service.get_issues_by_channel_id("ch1")
        self.assertEqual(len(result), 2)

    async def test_get_issues_by_sender_pagination(self):
        rows = [FakeIssueRow(sender="bob", discord_message_id=str(i)) for i in range(10)]
        service = self._make_service(rows)
        result = await service.get_issues_by_sender("bob", skip=2, limit=3)
        self.assertEqual(result["count"], 10)
        self.assertEqual(len(result["data"]), 3)
        self.assertEqual(result["data"][0]["discord_message_id"], "2")

    async def test_row_to_dict_parses_attachments(self):
        attachments = [{"attachment_name": "screenshot", "size_bytes": 1024}]
        row = FakeIssueRow(attachments=attachments)
        service = self._make_service([row])
        result = await service.get_issue_by_message_id(row.discord_message_id)
        self.assertEqual(len(result["attachments"]), 1)
        self.assertEqual(result["attachments"][0]["attachment_name"], "screenshot")


class ReplyToIssueTests(unittest.IsolatedAsyncioTestCase):
    """Tests for reply_to_issue service method."""

    def _make_service(self, rows=None, gateway=None):
        from discord_mcp.api.service import IssueQueryService

        return IssueQueryService(FakeRepository(rows), gateway or FakeGateway())

    async def test_returns_none_when_issue_not_found(self):
        service = self._make_service()
        result = await service.reply_to_issue("nonexistent", "reply")
        self.assertIsNone(result)

    async def test_persists_reply_as_new_record(self):
        row = FakeIssueRow(discord_message_id="123", channel_id="987654321")
        gateway = FakeGateway(
            reply_result=ReplyMessageResult(
                success=True,
                message_id="999",
                reply_to_message_id="123",
                channel_id="987654321",
                timestamp="2026-07-24T10:15:30+00:00",
            )
        )
        service = self._make_service([row], gateway)

        result = await service.reply_to_issue("123", "Issue resolved")

        self.assertIsNotNone(result)
        self.assertTrue(result["success"])
        self.assertTrue(result["message_sent"])
        self.assertEqual(result["data"]["discord_message_id"], "999")
        self.assertEqual(result["data"]["channel_id"], "987654321")
        self.assertEqual(result["data"]["sender"], "BOT")
        self.assertEqual(result["data"]["issue"], "Issue resolved")

    async def test_reply_uses_original_issue_metadata(self):
        row = FakeIssueRow(
            discord_message_id="123",
            guild_id="g1",
            guild_name="Test Guild",
            channel_id="987654321",
            channel_name="support",
        )
        service = self._make_service([row])

        await service.reply_to_issue("123", "Fixed")

        # Verify the new record was inserted with original metadata
        new_row = await service.get_issue_by_message_id("999")
        self.assertIsNotNone(new_row)
        self.assertEqual(new_row["guild_id"], "g1")
        self.assertEqual(new_row["guild_name"], "Test Guild")
        self.assertEqual(new_row["channel_name"], "support")

    async def test_reply_sets_parent_message_id(self):
        row = FakeIssueRow(discord_message_id="123", channel_id="987654321")
        service = self._make_service([row])

        result = await service.reply_to_issue("123", "Issue resolved")

        self.assertIsNotNone(result)
        self.assertEqual(result["data"]["parent_message_id"], "123")
        self.assertEqual(result["data"]["discord_message_id"], "999")

        # Verify the stored record also has parent_message_id
        new_row = await service.get_issue_by_message_id("999")
        self.assertEqual(new_row["parent_message_id"], "123")

    async def test_original_issue_not_modified_by_reply(self):
        row = FakeIssueRow(discord_message_id="123", channel_id="987654321")
        service = self._make_service([row])

        await service.reply_to_issue("123", "Reply")

        original = await service.get_issue_by_message_id("123")
        self.assertIsNone(original["parent_message_id"])

    async def test_handles_discord_failure(self):
        row = FakeIssueRow(discord_message_id="123", channel_id="987654321")

        gateway = AsyncMock()
        gateway.reply_message = AsyncMock(side_effect=RuntimeError("MCP error"))

        service = self._make_service([row], gateway)

        with self.assertRaises(RuntimeError):
            await service.reply_to_issue("123", "reply")


class DeleteIssueMessageTests(unittest.IsolatedAsyncioTestCase):
    """Tests for delete_issue_message service method."""

    def _make_service(self, rows=None, gateway=None):
        from discord_mcp.api.service import IssueQueryService

        return IssueQueryService(FakeRepository(rows), gateway or FakeGateway())

    async def test_returns_none_when_issue_not_found(self):
        service = self._make_service()
        result = await service.delete_issue_message("nonexistent")
        self.assertIsNone(result)

    async def test_deletes_discord_and_db_record(self):
        row = FakeIssueRow(discord_message_id="123", channel_id="987654321")
        service = self._make_service([row])

        result = await service.delete_issue_message("123")

        self.assertIsNotNone(result)
        self.assertTrue(result["success"])
        self.assertTrue(result["message_deleted"])
        self.assertTrue(result["database_record_deleted"])

        # Verify record was removed from DB
        remaining = await service.get_issue_by_message_id("123")
        self.assertIsNone(remaining)

    async def test_db_record_unchanged_on_discord_failure(self):
        row = FakeIssueRow(discord_message_id="123", channel_id="987654321")

        gateway = AsyncMock()
        gateway.delete_message = AsyncMock(side_effect=RuntimeError("MCP error"))

        service = self._make_service([row], gateway)

        with self.assertRaises(RuntimeError):
            await service.delete_issue_message("123")

        # Verify record still exists
        remaining = await service.get_issue_by_message_id("123")
        self.assertIsNotNone(remaining)


if __name__ == "__main__":
    unittest.main()
