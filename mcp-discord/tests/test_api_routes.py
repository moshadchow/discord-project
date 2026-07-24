"""Unit tests for API route handlers."""

import json
import unittest
from datetime import date, datetime, time
from unittest.mock import AsyncMock

from discord_mcp.api.mcp_models import DeleteMessageResult, ReplyMessageResult


class FakeIssueRow:
    """Minimal IssueRow stand-in for route tests."""

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
    """In-memory repository for route tests."""

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
    """In-memory gateway for route tests."""

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


def _create_test_app(rows=None, gateway=None):
    """Create a FastAPI test app with mocked dependencies."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from discord_mcp.api.deps import get_discord_gateway, get_issue_service
    from discord_mcp.api.routes import issue_router
    from discord_mcp.api.service import IssueQueryService

    app = FastAPI()
    app.include_router(issue_router, prefix="/api")

    repo = FakeRepository(rows)
    gw = gateway or FakeGateway()
    service = IssueQueryService(repo, gw)

    async def override_service():
        return service

    async def override_gateway():
        return gw

    app.dependency_overrides[get_issue_service] = override_service
    app.dependency_overrides[get_discord_gateway] = override_gateway
    return app, TestClient(app)


class GetIssueByMessageTests(unittest.TestCase):
    """Tests for GET /api/issues/message/{id}."""

    def test_returns_404_when_not_found(self):
        app, client = _create_test_app([])
        response = client.get("/api/issues/message/nonexistent")
        self.assertEqual(response.status_code, 404)

    def test_returns_issue_when_found(self):
        row = FakeIssueRow(discord_message_id="123")
        app, client = _create_test_app([row])
        response = client.get("/api/issues/message/123")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["discord_message_id"], "123")


class GetIssuesByChannelTests(unittest.TestCase):
    """Tests for GET /api/issues/channel/{id}."""

    def test_returns_list(self):
        rows = [
            FakeIssueRow(channel_id="ch1", discord_message_id="1"),
            FakeIssueRow(channel_id="ch1", discord_message_id="2"),
        ]
        app, client = _create_test_app(rows)
        response = client.get("/api/issues/channel/ch1")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 2)
        self.assertEqual(len(data["data"]), 2)

    def test_returns_empty_list(self):
        app, client = _create_test_app([])
        response = client.get("/api/issues/channel/empty")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 0)


class GetIssuesBySenderTests(unittest.TestCase):
    """Tests for GET /api/issues/sender/{name}."""

    def test_returns_paginated_results(self):
        rows = [FakeIssueRow(sender="bob", discord_message_id=str(i)) for i in range(5)]
        app, client = _create_test_app(rows)
        response = client.get("/api/issues/sender/bob?skip=1&limit=2")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 5)
        self.assertEqual(len(data["data"]), 2)


class ReplyToIssueTests(unittest.TestCase):
    """Tests for POST /api/issues/reply."""

    def test_returns_404_when_issue_not_found(self):
        app, client = _create_test_app([])
        response = client.post(
            "/api/issues/reply",
            json={"discord_message_id": "nonexistent", "message": "hi"},
        )
        self.assertEqual(response.status_code, 404)

    def test_returns_success_and_persists_reply(self):
        gateway = FakeGateway(
            reply_result=ReplyMessageResult(
                success=True,
                message_id="999",
                reply_to_message_id="123",
                channel_id="987654321",
                timestamp="2026-07-24T10:15:30+00:00",
            )
        )
        row = FakeIssueRow(discord_message_id="123", channel_id="987654321")
        app, client = _create_test_app([row], gateway=gateway)
        response = client.post(
            "/api/issues/reply",
            json={"discord_message_id": "123", "message": "Issue resolved"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["message_sent"])
        self.assertEqual(data["data"]["discord_message_id"], "999")
        self.assertEqual(data["data"]["channel_id"], "987654321")
        self.assertEqual(data["data"]["sender"], "BOT")

    def test_returns_500_when_discord_fails(self):
        gateway = AsyncMock()
        gateway.reply_message = AsyncMock(side_effect=RuntimeError("MCP error"))

        row = FakeIssueRow(discord_message_id="123", channel_id="987654321")
        app, client = _create_test_app([row], gateway=gateway)
        response = client.post(
            "/api/issues/reply",
            json={"discord_message_id": "123", "message": "reply"},
        )
        self.assertEqual(response.status_code, 500)


class DeleteIssueMessageTests(unittest.TestCase):
    """Tests for DELETE /api/issues/message/{id}."""

    def test_returns_404_when_issue_not_found(self):
        app, client = _create_test_app([])
        response = client.delete("/api/issues/message/nonexistent")
        self.assertEqual(response.status_code, 404)

    def test_returns_success_when_deleted(self):
        gateway = FakeGateway(
            delete_result=DeleteMessageResult(
                success=True,
                message_id="123",
                channel_id="987654321",
                message_deleted=True,
            )
        )
        row = FakeIssueRow(discord_message_id="123", channel_id="987654321")
        app, client = _create_test_app([row], gateway=gateway)
        response = client.delete("/api/issues/message/123")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["discord_message_id"], "123")
        self.assertEqual(data["channel_id"], "987654321")
        self.assertTrue(data["message_deleted"])
        self.assertTrue(data["database_record_deleted"])

    def test_returns_500_when_discord_fails(self):
        gateway = AsyncMock()
        gateway.delete_message = AsyncMock(side_effect=RuntimeError("MCP error"))

        row = FakeIssueRow(discord_message_id="123", channel_id="987654321")
        app, client = _create_test_app([row], gateway=gateway)
        response = client.delete("/api/issues/message/123")
        self.assertEqual(response.status_code, 500)


if __name__ == "__main__":
    unittest.main()
