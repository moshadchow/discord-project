import os
import sys
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, List
from functools import wraps
import discord
from discord.ext import commands
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
from .config import load_database_config, load_monitored_channels_config
from .issue_capture import IssueCaptureService
from .issues_repository import IssuesRepository

def _configure_windows_stdout_encoding():
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

_configure_windows_stdout_encoding()
load_dotenv(override=False)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord-mcp-server")

# Discord bot setup
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is required")

# Initialize Discord bot with necessary intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize MCP server
app = Server("discord-server")

# Store Discord client reference
discord_client = None
bot_ready_event = asyncio.Event()
issue_capture_service = IssueCaptureService(None, logger)
monitored_channels_config = load_monitored_channels_config()

@bot.event
async def on_ready():
    global discord_client
    discord_client = bot
    bot_ready_event.set()
    logger.info(f"Logged in as {bot.user.name}")
    _log_monitored_channel_validation()

@bot.event
async def on_message(message):
    await bot_ready_event.wait()

    if bot.user and message.author.id == bot.user.id:
        return

    try:
        if _should_capture_message(message):
            await issue_capture_service.capture_message(message)
    except Exception:
        logger.exception(
            "Unhandled issue capture failure",
            extra={"discord_message_id": str(getattr(message, "id", ""))},
        )

    await bot.process_commands(message)


@bot.event
async def on_message_delete(message):
    await bot_ready_event.wait()

    try:
        if message.guild is None:
            return

        if not monitored_channels_config.enabled:
            return

        if not monitored_channels_config.matches_channel(message.channel):
            return

        await issue_capture_service.delete_message(str(message.id))
    except Exception:
        logger.exception(
            "Unhandled message deletion failure",
            extra={"discord_message_id": str(getattr(message, "id", ""))},
        )


def _should_capture_message(message: object) -> bool:
    message_id = str(getattr(message, "id", ""))
    channel = getattr(message, "channel", None)
    guild = getattr(message, "guild", None)
    channel_id = str(getattr(channel, "id", "")) if channel else ""
    channel_name = getattr(channel, "name", None) if channel else None

    if guild is None:
        logger.info(
            "Message ignored because direct messages are not monitored",
            extra={
                "discord_message_id": message_id,
                "channel_id": channel_id,
            },
        )
        return False

    if not monitored_channels_config.enabled:
        logger.info(
            "Message ignored because no monitored Discord channels are configured",
            extra={
                "discord_message_id": message_id,
                "guild_id": str(getattr(guild, "id", "")),
                "channel_id": channel_id,
                "channel_name": channel_name,
            },
        )
        return False

    if not monitored_channels_config.matches_channel(channel):
        logger.info(
            "Message ignored because channel is not configured for issue capture",
            extra={
                "discord_message_id": message_id,
                "guild_id": str(getattr(guild, "id", "")),
                "channel_id": channel_id,
                "channel_name": channel_name,
            },
        )
        return False

    logger.info(
        "Message accepted for issue capture",
        extra={
            "discord_message_id": message_id,
            "guild_id": str(getattr(guild, "id", "")),
            "channel_id": channel_id,
            "channel_name": channel_name,
        },
    )
    return True


def _log_monitored_channel_validation() -> None:
    logger.info(
        "Configured monitored Discord channels",
        extra={
            "channel_ids": sorted(monitored_channels_config.channel_ids),
            "channel_names": sorted(monitored_channels_config.channel_names),
        },
    )

    if not monitored_channels_config.enabled:
        logger.warning("No monitored Discord channels configured for issue capture")
        return

    visible_channel_ids = {
        str(channel.id)
        for guild in bot.guilds
        for channel in getattr(guild, "text_channels", [])
    }
    visible_channel_names = {
        str(channel.name)
        for guild in bot.guilds
        for channel in getattr(guild, "text_channels", [])
    }

    for channel_id in sorted(monitored_channels_config.channel_ids - visible_channel_ids):
        logger.warning(
            "Configured monitored Discord channel ID was not found",
            extra={"channel_id": channel_id},
        )

    for channel_name in sorted(monitored_channels_config.channel_names - visible_channel_names):
        logger.warning(
            "Configured monitored Discord channel name was not found",
            extra={"channel_name": channel_name},
        )

# Helper function to ensure Discord client is ready
def require_discord_client(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        await bot_ready_event.wait()
        if not discord_client:
            raise RuntimeError("Discord client not ready")
        return await func(*args, **kwargs)
    return wrapper

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available Discord tools."""
    return [
        # Server Information Tools
        Tool(
            name="get_server_info",
            description="Get information about a Discord server",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server (guild) ID"
                    }
                },
                "required": ["server_id"]
            }
        ),
        Tool(
            name="get_channels",
            description="Get a list of all channels in a Discord server",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server (guild) ID"
                    }
                },
                "required": ["server_id"]
            }
        ),
        Tool(
            name="list_members",
            description="Get a list of members in a server",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server (guild) ID"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of members to fetch",
                        "minimum": 1,
                        "maximum": 1000
                    }
                },
                "required": ["server_id"]
            }
        ),

        # Role Management Tools
        Tool(
            name="add_role",
            description="Add a role to a user",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server ID"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "User to add role to"
                    },
                    "role_id": {
                        "type": "string",
                        "description": "Role ID to add"
                    }
                },
                "required": ["server_id", "user_id", "role_id"]
            }
        ),
        Tool(
            name="remove_role",
            description="Remove a role from a user",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server ID"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "User to remove role from"
                    },
                    "role_id": {
                        "type": "string",
                        "description": "Role ID to remove"
                    }
                },
                "required": ["server_id", "user_id", "role_id"]
            }
        ),

        # Channel Management Tools
        Tool(
            name="create_text_channel",
            description="Create a new text channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server ID"
                    },
                    "name": {
                        "type": "string",
                        "description": "Channel name"
                    },
                    "category_id": {
                        "type": "string",
                        "description": "Optional category ID to place channel in"
                    },
                    "topic": {
                        "type": "string",
                        "description": "Optional channel topic"
                    }
                },
                "required": ["server_id", "name"]
            }
        ),
        Tool(
            name="delete_channel",
            description="Delete a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "ID of channel to delete"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for deletion"
                    }
                },
                "required": ["channel_id"]
            }
        ),

        # Message Reaction Tools
        Tool(
            name="reply_message",
            description="Reply to an existing Discord message using its discord_message_id",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Discord channel containing the original message"
                    },
                    "discord_message_id": {
                        "type": "string",
                        "description": "Discord message ID to reply to"
                    },
                    "message": {
                        "type": "string",
                        "description": "Reply message"
                    }
                },
                "required": ["channel_id", "discord_message_id", "message"]
            }
        ),
        Tool(
            name="add_reaction",
            description="Add a reaction to a message",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Channel containing the message"
                    },
                    "message_id": {
                        "type": "string",
                        "description": "Message to react to"
                    },
                    "emoji": {
                        "type": "string",
                        "description": "Emoji to react with (Unicode or custom emoji ID)"
                    }
                },
                "required": ["channel_id", "message_id", "emoji"]
            }
        ),
        Tool(
            name="add_multiple_reactions",
            description="Add multiple reactions to a message",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Channel containing the message"
                    },
                    "message_id": {
                        "type": "string",
                        "description": "Message to react to"
                    },
                    "emojis": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "Emoji to react with (Unicode or custom emoji ID)"
                        },
                        "description": "List of emojis to add as reactions"
                    }
                },
                "required": ["channel_id", "message_id", "emojis"]
            }
        ),
        Tool(
            name="remove_reaction",
            description="Remove a reaction from a message",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Channel containing the message"
                    },
                    "message_id": {
                        "type": "string",
                        "description": "Message to remove reaction from"
                    },
                    "emoji": {
                        "type": "string",
                        "description": "Emoji to remove (Unicode or custom emoji ID)"
                    }
                },
                "required": ["channel_id", "message_id", "emoji"]
            }
        ),
        Tool(
            name="send_message",
            description="Send a message to a specific channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Discord channel ID"
                    },
                    "content": {
                        "type": "string",
                        "description": "Message content"
                    }
                },
                "required": ["channel_id", "content"]
            }
        ),
        Tool(
            name="read_messages",
            description="Read recent messages from a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Discord channel ID"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Number of messages to fetch (max 100)",
                        "minimum": 1,
                        "maximum": 100
                    }
                },
                "required": ["channel_id"]
            }
        ),
        Tool(
            name="get_user_info",
            description="Get information about a Discord user",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "Discord user ID"
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="moderate_message",
            description="Delete a message and optionally timeout the user",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Channel ID containing the message"
                    },
                    "message_id": {
                        "type": "string",
                        "description": "ID of message to moderate"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for moderation"
                    },
                    "timeout_minutes": {
                        "type": "number",
                        "description": "Optional timeout duration in minutes",
                        "minimum": 0,
                        "maximum": 40320  # Max 4 weeks
                    }
                },
                "required": ["channel_id", "message_id", "reason"]
            }
        ),
        Tool(
            name="list_servers",
            description="Get a list of all Discord servers the bot has access to with their details such as name, id, member count, and creation date.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@app.call_tool()
@require_discord_client
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle Discord tool calls."""
    
    if name == "send_message":
        channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
        message = await channel.send(arguments["content"])
        return [TextContent(
            type="text",
            text=f"Message sent successfully. Message ID: {message.id}"
        )]

    elif name == "reply_message":
        channel_id = arguments["channel_id"]
        discord_message_id = arguments["discord_message_id"]
        message_content = arguments["message"]

        logger.info(
            "Reply request received",
            extra={"channel_id": channel_id, "discord_message_id": discord_message_id},
        )

        try:
            channel = await discord_client.fetch_channel(int(channel_id))
        except discord.NotFound:
            logger.error("Channel not found", extra={"channel_id": channel_id})
            return [TextContent(type="text", text="Error: Channel not found")]
        except discord.Forbidden:
            logger.error("Missing permissions for channel", extra={"channel_id": channel_id})
            return [TextContent(type="text", text="Error: Missing permissions to access channel")]

        logger.info("Channel retrieved", extra={"channel_id": channel_id, "channel_name": getattr(channel, "name", "")})

        try:
            original_message = await channel.fetch_message(int(discord_message_id))
        except discord.NotFound:
            logger.error("Message not found", extra={"discord_message_id": discord_message_id})
            return [TextContent(type="text", text="Error: Message not found")]
        except discord.Forbidden:
            logger.error("Missing permissions to read message", extra={"discord_message_id": discord_message_id})
            return [TextContent(type="text", text="Error: Missing permissions to read message")]

        logger.info("Original message retrieved", extra={"discord_message_id": discord_message_id, "author": str(original_message.author)})

        try:
            reply = await original_message.reply(content=message_content, mention_author=False)
        except discord.Forbidden:
            logger.error("Missing permissions to send reply", extra={"channel_id": channel_id})
            return [TextContent(type="text", text="Error: Missing permissions to send reply")]
        except discord.HTTPException as e:
            logger.error("Discord API error sending reply", extra={"error": str(e)})
            return [TextContent(type="text", text=f"Error: Discord API error - {e}")]
        except Exception as e:
            logger.exception("Unexpected error sending reply")
            return [TextContent(type="text", text="Error: Unexpected error sending reply")]

        logger.info(
            "Reply sent successfully",
            extra={
                "channel_id": channel_id,
                "new_message_id": str(reply.id),
                "reply_to_message_id": discord_message_id,
            },
        )

        response = json.dumps({
            "success": True,
            "message_id": str(reply.id),
            "reply_to_message_id": discord_message_id,
            "channel_id": channel_id,
            "timestamp": reply.created_at.isoformat(),
        })
        return [TextContent(type="text", text=response)]

    elif name == "read_messages":
        channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
        limit = min(int(arguments.get("limit", 10)), 100)
        fetch_users = arguments.get("fetch_reaction_users", False)  # Only fetch users if explicitly requested
        messages = []
        async for message in channel.history(limit=limit):
            reaction_data = []
            for reaction in message.reactions:
                emoji_str = str(reaction.emoji.name) if hasattr(reaction.emoji, 'name') and reaction.emoji.name else str(reaction.emoji.id) if hasattr(reaction.emoji, 'id') else str(reaction.emoji)
                reaction_info = {
                    "emoji": emoji_str,
                    "count": reaction.count
                }
                logger.error(f"Emoji: {emoji_str}")
                reaction_data.append(reaction_info)
            messages.append({
                "id": str(message.id),
                "author": str(message.author),
                "content": message.content,
                "timestamp": message.created_at.isoformat(),
                "reactions": reaction_data  # Add reactions to message dict
            })
        # Helper function to format reactions
        def format_reaction(r):
            return f"{r['emoji']}({r['count']})"
            
        return [TextContent(
            type="text",
            text=f"Retrieved {len(messages)} messages:\n\n" + 
                 "\n".join([
                     f"{m['author']} ({m['timestamp']}): {m['content']}\n" +
                     f"Reactions: {', '.join([format_reaction(r) for r in m['reactions']]) if m['reactions'] else 'No reactions'}"
                     for m in messages
                 ])
        )]

    elif name == "get_user_info":
        user = await discord_client.fetch_user(int(arguments["user_id"]))
        user_info = {
            "id": str(user.id),
            "name": user.name,
            "discriminator": user.discriminator,
            "bot": user.bot,
            "created_at": user.created_at.isoformat()
        }
        return [TextContent(
            type="text",
            text=f"User information:\n" + 
                 f"Name: {user_info['name']}#{user_info['discriminator']}\n" +
                 f"ID: {user_info['id']}\n" +
                 f"Bot: {user_info['bot']}\n" +
                 f"Created: {user_info['created_at']}"
        )]

    elif name == "moderate_message":
        channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
        message = await channel.fetch_message(int(arguments["message_id"]))

        # Delete the message
        await message.delete()

        timed_out = False
        # Handle timeout if specified
        if "timeout_minutes" in arguments and arguments["timeout_minutes"] > 0:
            if isinstance(message.author, discord.Member):
                duration = discord.utils.utcnow() + timedelta(
                    minutes=arguments["timeout_minutes"]
                )
                await message.author.timeout(
                    duration,
                    reason=arguments["reason"]
                )
                timed_out = True

        response = json.dumps({
            "success": True,
            "message_id": str(message.id),
            "channel_id": str(channel.id),
            "message_deleted": True,
            "timed_out": timed_out,
        })
        return [TextContent(type="text", text=response)]

    # Server Information Tools
    elif name == "get_server_info":
        guild = await discord_client.fetch_guild(int(arguments["server_id"]))
        info = {
            "name": guild.name,
            "id": str(guild.id),
            "owner_id": str(guild.owner_id),
            "member_count": guild.member_count,
            "created_at": guild.created_at.isoformat(),
            "description": guild.description,
            "premium_tier": guild.premium_tier,
            "explicit_content_filter": str(guild.explicit_content_filter)
        }
        return [TextContent(
            type="text",
            text=f"Server Information:\n" + "\n".join(f"{k}: {v}" for k, v in info.items())
        )]

    elif name == "get_channels":
        try:
            guild = discord_client.get_guild(int(arguments["server_id"]))
            if guild:
                channel_list = []
                for channel in guild.channels:
                    channel_list.append(f"#{channel.name} (ID: {channel.id}) - {channel.type}")
                
                return [TextContent(
                    type="text", 
                    text=f"Channels in {guild.name}:\n" + "\n".join(channel_list)
                )]
            else:
                return [TextContent(type="text", text="Guild not found")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    elif name == "list_members":
        guild = await discord_client.fetch_guild(int(arguments["server_id"]))
        limit = min(int(arguments.get("limit", 100)), 1000)
        
        members = []
        async for member in guild.fetch_members(limit=limit):
            members.append({
                "id": str(member.id),
                "name": member.name,
                "nick": member.nick,
                "joined_at": member.joined_at.isoformat() if member.joined_at else None,
                "roles": [str(role.id) for role in member.roles[1:]]  # Skip @everyone
            })
        
        return [TextContent(
            type="text",
            text=f"Server Members ({len(members)}):\n" + 
                 "\n".join(f"{m['name']} (ID: {m['id']}, Roles: {', '.join(m['roles'])})" for m in members)
        )]

    # Role Management Tools
    elif name == "add_role":
        guild = await discord_client.fetch_guild(int(arguments["server_id"]))
        member = await guild.fetch_member(int(arguments["user_id"]))
        role = guild.get_role(int(arguments["role_id"]))
        
        await member.add_roles(role, reason="Role added via MCP")
        return [TextContent(
            type="text",
            text=f"Added role {role.name} to user {member.name}"
        )]

    elif name == "remove_role":
        guild = await discord_client.fetch_guild(int(arguments["server_id"]))
        member = await guild.fetch_member(int(arguments["user_id"]))
        role = guild.get_role(int(arguments["role_id"]))
        
        await member.remove_roles(role, reason="Role removed via MCP")
        return [TextContent(
            type="text",
            text=f"Removed role {role.name} from user {member.name}"
        )]

    # Channel Management Tools
    elif name == "create_text_channel":
        guild = await discord_client.fetch_guild(int(arguments["server_id"]))
        category = None
        if "category_id" in arguments:
            category = guild.get_channel(int(arguments["category_id"]))
        
        channel = await guild.create_text_channel(
            name=arguments["name"],
            category=category,
            topic=arguments.get("topic"),
            reason="Channel created via MCP"
        )
        
        return [TextContent(
            type="text",
            text=f"Created text channel #{channel.name} (ID: {channel.id})"
        )]

    elif name == "delete_channel":
        channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
        await channel.delete(reason=arguments.get("reason", "Channel deleted via MCP"))
        return [TextContent(
            type="text",
            text=f"Deleted channel successfully"
        )]

    # Message Reaction Tools
    elif name == "add_reaction":
        channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
        message = await channel.fetch_message(int(arguments["message_id"]))
        await message.add_reaction(arguments["emoji"])
        return [TextContent(
            type="text",
            text=f"Added reaction {arguments['emoji']} to message"
        )]

    elif name == "add_multiple_reactions":
        channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
        message = await channel.fetch_message(int(arguments["message_id"]))
        for emoji in arguments["emojis"]:
            await message.add_reaction(emoji)
        return [TextContent(
            type="text",
            text=f"Added reactions: {', '.join(arguments['emojis'])} to message"
        )]

    elif name == "remove_reaction":
        channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
        message = await channel.fetch_message(int(arguments["message_id"]))
        await message.remove_reaction(arguments["emoji"], discord_client.user)
        return [TextContent(
            type="text",
            text=f"Removed reaction {arguments['emoji']} from message"
        )]

    elif name == "list_servers":
        servers = []
        for guild in discord_client.guilds:
            servers.append({
                "id": str(guild.id),
                "name": guild.name,
                "member_count": guild.member_count,
                "created_at": guild.created_at.isoformat()
            })
        
        return [TextContent(
            type="text",
            text=f"Available Servers ({len(servers)}):\n" + 
                 "\n".join(f"{s['name']} (ID: {s['id']}, Members: {s['member_count']})" for s in servers)
        )]

    raise ValueError(f"Unknown tool: {name}")

async def main():
    global issue_capture_service

    repository = None
    database_config = load_database_config()
    if database_config.capture_enabled:
        try:
            repository = IssuesRepository(database_config.database_url)
            await repository.open()
            issue_capture_service = IssueCaptureService(repository, logger)
            logger.info("Discord issue capture enabled")
        except Exception:
            if repository:
                await repository.close()
            repository = None
            issue_capture_service = IssueCaptureService(None, logger)
            logger.exception("Discord issue capture disabled after database initialization failure")
    else:
        logger.info("Discord issue capture disabled because DATABASE_URL is not set")

    bot_task = asyncio.create_task(bot.start(DISCORD_TOKEN))

    api_task = None
    if database_config.capture_enabled:
        try:
            import uvicorn

            from .api import create_app

            api_app = create_app()
            api_config = uvicorn.Config(
                api_app, host="0.0.0.0", port=8000, log_level="info"
            )
            api_server = uvicorn.Server(api_config)
            api_task = asyncio.create_task(api_server.serve())
            logger.info("FastAPI REST API starting on port 8000")
        except Exception:
            logger.exception("Failed to start FastAPI server")

    try:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    finally:
        if api_task:
            api_task.cancel()
        if repository:
            await repository.close()
        await bot.close()
        if not bot_task.done():
            bot_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
