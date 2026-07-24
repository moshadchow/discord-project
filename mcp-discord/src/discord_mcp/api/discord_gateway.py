"""Discord Gateway — abstraction layer for invoking MCP tools."""

import json
import logging

from .mcp_models import DeleteMessageResult, ReplyMessageResult

logger = logging.getLogger("discord-mcp-api.gateway")


class DiscordGateway:
    """Translates service-layer requests into MCP tool calls.

    No business logic. No SQLModel. No FastAPI.
    Only responsible for communicating with the MCP server.
    """

    async def reply_message(
        self, channel_id: str, discord_message_id: str, message: str
    ) -> ReplyMessageResult:
        """Reply to a Discord message via the reply_message MCP tool."""
        from ..server import call_tool

        logger.info(
            "MCP reply_message request",
            extra={"channel_id": channel_id, "discord_message_id": discord_message_id},
        )

        result = await call_tool(
            "reply_message",
            {
                "channel_id": channel_id,
                "discord_message_id": discord_message_id,
                "message": message,
            },
        )

        data = json.loads(result[0].text)

        if not data.get("success"):
            error_msg = data.get("error", "Unknown MCP error")
            logger.error("MCP reply_message failed", extra={"error": error_msg})
            raise RuntimeError(f"MCP reply_message failed: {error_msg}")

        logger.info(
            "MCP reply_message succeeded",
            extra={"new_message_id": data["message_id"]},
        )

        return ReplyMessageResult(**data)

    async def delete_message(
        self, channel_id: str, message_id: str, reason: str = "Deleted via API"
    ) -> DeleteMessageResult:
        """Delete a Discord message via the moderate_message MCP tool."""
        from ..server import call_tool

        logger.info(
            "MCP moderate_message request",
            extra={"channel_id": channel_id, "message_id": message_id},
        )

        result = await call_tool(
            "moderate_message",
            {
                "channel_id": channel_id,
                "message_id": message_id,
                "reason": reason,
            },
        )

        data = json.loads(result[0].text)

        if not data.get("success"):
            error_msg = data.get("error", "Unknown MCP error")
            logger.error("MCP moderate_message failed", extra={"error": error_msg})
            raise RuntimeError(f"MCP moderate_message failed: {error_msg}")

        logger.info(
            "MCP moderate_message succeeded",
            extra={"message_id": data["message_id"]},
        )

        return DeleteMessageResult(**data)
