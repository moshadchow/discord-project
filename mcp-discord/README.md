# Discord MCP Server

[![smithery badge](https://smithery.ai/badge/@hanweg/mcp-discord)](https://smithery.ai/server/@hanweg/mcp-discord)
A Model Context Protocol (MCP) server that provides Discord integration capabilities to MCP clients like Claude Desktop.

<a href="https://glama.ai/mcp/servers/wvwjgcnppa"><img width="380" height="200" src="https://glama.ai/mcp/servers/wvwjgcnppa/badge" alt="mcp-discord MCP server" /></a>

## Available Tools

### Server Information
- `list_servers`: List available servers
- `get_server_info`: Get detailed server information
- `get_channels`: List channels in a server
- `list_members`: List server members and their roles
- `get_user_info`: Get detailed information about a user

### Message Management
- `send_message`: Send a message to a channel
- `read_messages`: Read recent message history
- `add_reaction`: Add a reaction to a message
- `add_multiple_reactions`: Add multiple reactions to a message
- `remove_reaction`: Remove a reaction from a message
- `moderate_message`: Delete messages and timeout users

### Channel Management
- `create_text_channel`: Create a new text channel
- `delete_channel`: Delete an existing channel

### Role Management
- `add_role`: Add a role to a user
- `remove_role`: Remove a role from a user

## Automatic Issue Capture

When `DATABASE_URL` is set, the Discord bot can listen for new non-bot messages in configured channels and save each message as an issue record in PostgreSQL. If `DATABASE_URL` is not set, this capture feature is disabled and the existing MCP tools continue to work normally.

The server creates the `issues` table automatically if it does not already exist. Each Discord message is stored once using `discord_message_id` as a unique key.

Required PostgreSQL configuration:

```bash
DATABASE_URL=postgresql://user:password@host:5432/database
```

Configure monitored channels by ID, name, or both. Channel IDs are preferred because Discord channel names can change.

```bash
DISCORD_MONITORED_CHANNEL_IDS=123456789012345678,987654321098765432
DISCORD_MONITORED_CHANNELS=support-issues,production-alerts
```

If no monitored channels are configured, automatic issue capture ignores incoming messages.

Local `.env` files are loaded automatically when the server starts. Shell or MCP client environment variables take precedence over `.env` values.

Example `.env`:

```env
DISCORD_TOKEN=your_discord_bot_token
DATABASE_URL=postgresql://user:password@localhost:5432/database
DISCORD_MONITORED_CHANNEL_IDS=123456789012345678
```

Schema summary:

```text
issues
------
id
discord_message_id
guild_id
guild_name
channel_id
channel_name
sender
issue_date
issue_time
issue
message_timestamp
message_timestamp_local
created_at
updated_at
```

## Installation

1. Set up your Discord bot:
   - Create a new application at [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a bot and copy the token
   - Enable required privileged intents:
     - MESSAGE CONTENT INTENT
     - PRESENCE INTENT
     - SERVER MEMBERS INTENT
   - Invite the bot to your server using OAuth2 URL Generator

2. Clone and install the package:
```bash
# Clone the repository
git clone https://github.com/hanweg/mcp-discord.git
cd mcp-discord

# Create and activate virtual environment
uv venv
.venv\Scripts\activate # On macOS/Linux, use: source .venv/bin/activate

### If using Python 3.13+ - install audioop library: `uv pip install audioop-lts`

# Install the package
uv pip install -e .
```

3. Configure Claude Desktop (`%APPDATA%\Claude\claude_desktop_config.json` on Windows, `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):
```json
    "discord": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\PATH\\TO\\mcp-discord",
        "run",
        "mcp-discord"
      ],
      "env": {
        "DISCORD_TOKEN": "your_bot_token",
        "DATABASE_URL": "postgresql://user:password@host:5432/database"
      }
    }
```

### Installing via Smithery

To install Discord Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@hanweg/mcp-discord):

```bash
npx -y @smithery/cli install @hanweg/mcp-discord --client claude
```

## License

MIT License - see LICENSE file for details.
