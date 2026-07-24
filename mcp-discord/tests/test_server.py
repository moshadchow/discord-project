"""Unit tests for MCP server tools, specifically reply_message."""

import json
import unittest
from unittest.mock import AsyncMock, patch

import discord


class ReplyMessageTests(unittest.IsolatedAsyncioTestCase):
    """Tests for the reply_message MCP tool."""

    def _make_mock_channel(self):
        channel = AsyncMock()
        channel.id = 123456789
        return channel

    def _make_mock_message(self):
        message = AsyncMock()
        message.id = 987654321
        message.created_at = AsyncMock()
        message.created_at.isoformat = lambda: "2026-07-24T10:15:30+00:00"
        return message

    def _make_mock_reply(self):
        reply = AsyncMock()
        reply.id = 111111111
        reply.created_at = AsyncMock()
        reply.created_at.isoformat = lambda: "2026-07-24T10:15:31+00:00"
        return reply

    @patch("discord_mcp.server.discord_client", new_callable=lambda: AsyncMock)
    @patch("discord_mcp.server.bot_ready_event")
    async def test_reply_message_success(self, mock_event, mock_client):
        mock_event.wait = AsyncMock()
        mock_channel = self._make_mock_channel()
        mock_message = self._make_mock_message()
        mock_reply = self._make_mock_reply()

        mock_client.fetch_channel = AsyncMock(return_value=mock_channel)
        mock_channel.fetch_message = AsyncMock(return_value=mock_message)
        mock_message.reply = AsyncMock(return_value=mock_reply)

        from discord_mcp.server import call_tool

        args = {
            "channel_id": "123456789",
            "discord_message_id": "987654321",
            "message": "This is a reply",
        }
        result = await call_tool("reply_message", args)

        self.assertEqual(len(result), 1)
        data = json.loads(result[0].text)
        self.assertTrue(data["success"])
        self.assertEqual(data["message_id"], "111111111")
        self.assertEqual(data["channel_id"], "123456789")
        self.assertEqual(data["reply_to_message_id"], "987654321")
        self.assertIn("timestamp", data)
        mock_message.reply.assert_awaited_once_with(content="This is a reply", mention_author=False)
        mock_channel.send.assert_not_awaited()

    @patch("discord_mcp.server.discord_client", new_callable=lambda: AsyncMock)
    @patch("discord_mcp.server.bot_ready_event")
    async def test_reply_message_invalid_channel(self, mock_event, mock_client):
        mock_event.wait = AsyncMock()
        mock_client.fetch_channel = AsyncMock(
            side_effect=discord.NotFound(AsyncMock(), "Channel not found")
        )

        from discord_mcp.server import call_tool

        args = {
            "channel_id": "999",
            "discord_message_id": "111",
            "message": "test",
        }
        result = await call_tool("reply_message", args)

        self.assertEqual(len(result), 1)
        self.assertIn("Channel not found", result[0].text)

    @patch("discord_mcp.server.discord_client", new_callable=lambda: AsyncMock)
    @patch("discord_mcp.server.bot_ready_event")
    async def test_reply_message_invalid_message(self, mock_event, mock_client):
        mock_event.wait = AsyncMock()
        mock_channel = self._make_mock_channel()
        mock_client.fetch_channel = AsyncMock(return_value=mock_channel)
        mock_channel.fetch_message = AsyncMock(
            side_effect=discord.NotFound(AsyncMock(), "Message not found")
        )

        from discord_mcp.server import call_tool

        args = {
            "channel_id": "123456789",
            "discord_message_id": "999",
            "message": "test",
        }
        result = await call_tool("reply_message", args)

        self.assertEqual(len(result), 1)
        self.assertIn("Message not found", result[0].text)

    @patch("discord_mcp.server.discord_client", new_callable=lambda: AsyncMock)
    @patch("discord_mcp.server.bot_ready_event")
    async def test_reply_message_missing_permissions_channel(self, mock_event, mock_client):
        mock_event.wait = AsyncMock()
        mock_client.fetch_channel = AsyncMock(
            side_effect=discord.Forbidden(AsyncMock(), "Forbidden")
        )

        from discord_mcp.server import call_tool

        args = {
            "channel_id": "123456789",
            "discord_message_id": "111",
            "message": "test",
        }
        result = await call_tool("reply_message", args)

        self.assertEqual(len(result), 1)
        self.assertIn("Missing permissions", result[0].text)

    @patch("discord_mcp.server.discord_client", new_callable=lambda: AsyncMock)
    @patch("discord_mcp.server.bot_ready_event")
    async def test_reply_message_missing_permissions_send(self, mock_event, mock_client):
        mock_event.wait = AsyncMock()
        mock_channel = self._make_mock_channel()
        mock_message = self._make_mock_message()
        mock_client.fetch_channel = AsyncMock(return_value=mock_channel)
        mock_channel.fetch_message = AsyncMock(return_value=mock_message)
        mock_message.reply = AsyncMock(
            side_effect=discord.Forbidden(AsyncMock(), "Forbidden")
        )

        from discord_mcp.server import call_tool

        args = {
            "channel_id": "123456789",
            "discord_message_id": "987654321",
            "message": "test",
        }
        result = await call_tool("reply_message", args)

        self.assertEqual(len(result), 1)
        self.assertIn("Missing permissions", result[0].text)

    @patch("discord_mcp.server.discord_client", new_callable=lambda: AsyncMock)
    @patch("discord_mcp.server.bot_ready_event")
    async def test_reply_message_discord_api_error(self, mock_event, mock_client):
        mock_event.wait = AsyncMock()
        mock_channel = self._make_mock_channel()
        mock_message = self._make_mock_message()
        mock_client.fetch_channel = AsyncMock(return_value=mock_channel)
        mock_channel.fetch_message = AsyncMock(return_value=mock_message)
        mock_message.reply = AsyncMock(
            side_effect=discord.HTTPException(AsyncMock(), "Rate limited")
        )

        from discord_mcp.server import call_tool

        args = {
            "channel_id": "123456789",
            "discord_message_id": "987654321",
            "message": "test",
        }
        result = await call_tool("reply_message", args)

        self.assertEqual(len(result), 1)
        self.assertIn("Discord API error", result[0].text)

    @patch("discord_mcp.server.discord_client", new_callable=lambda: AsyncMock)
    @patch("discord_mcp.server.bot_ready_event")
    async def test_reply_message_unexpected_exception(self, mock_event, mock_client):
        mock_event.wait = AsyncMock()
        mock_channel = self._make_mock_channel()
        mock_message = self._make_mock_message()
        mock_client.fetch_channel = AsyncMock(return_value=mock_channel)
        mock_channel.fetch_message = AsyncMock(return_value=mock_message)
        mock_message.reply = AsyncMock(side_effect=RuntimeError("Something broke"))

        from discord_mcp.server import call_tool

        args = {
            "channel_id": "123456789",
            "discord_message_id": "987654321",
            "message": "test",
        }
        result = await call_tool("reply_message", args)

        self.assertEqual(len(result), 1)
        self.assertIn("Unexpected error", result[0].text)


if __name__ == "__main__":
    unittest.main()
