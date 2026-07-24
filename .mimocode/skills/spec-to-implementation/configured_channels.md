# Enhance Discord Bot to Listen for Messages from Configured Channels

## Objective

Enhance the Discord bot to automatically listen for new messages using the existing Discord event system (`on_message`).

The bot should monitor **only the Discord channels configured in the `.env` file** and ignore messages from all other channels.

This functionality should integrate seamlessly with the existing MCP server without affecting current tool behavior.

---

# Configuration

Configure the channels to monitor using the `.env` file.

Example:

```env
DISCORD_MONITORED_CHANNELS=support-issues,production-alerts,oms-errors
```

or

```env
DISCORD_MONITORED_CHANNEL_IDS=123456789012345678,987654321098765432
```

> Prefer monitoring by **Channel ID** for reliability, as channel names can change over time.

The bot should load the configured channels during startup.

---

# Message Listener

Enhance the existing `on_message` event handler.

Requirements:

- Listen for every newly received Discord message.
- Process messages only after the bot is fully connected (`on_ready`).
- Ignore messages sent by the bot itself.
- Ignore Direct Messages (DMs).
- Ignore messages from channels that are not listed in the `.env` configuration.
- Continue supporting all existing MCP functionality without interruption.

---

# Channel Validation

Before processing a message:

1. Determine the channel ID (or channel name, depending on configuration).
2. Verify that the channel exists in the configured monitored channel list.
3. If the channel is not configured:
   - Ignore the message.
   - Do not perform issue extraction.
   - Do not write anything to the database.

---

# Message Processing

For messages received from configured channels:

- Extract issue information using the existing issue parser.
- Persist the issue to PostgreSQL using the existing repository/service.
- Continue using the existing duplicate detection mechanism based on Discord Message ID.

---

# Logging

Log the following events:

- Bot startup
- Configured monitored channels
- Channel validation result
- Message received
- Message ignored (non-configured channel)
- Issue extraction success/failure
- Database insert success/failure
- Duplicate message detected

Do not log sensitive information such as tokens or database credentials.

---

# Error Handling

- If processing a message fails:
  - Log the error.
  - Continue processing subsequent messages.
  - Do not terminate the Discord bot.

- If a configured channel cannot be found:
  - Log a warning during startup.
  - Continue monitoring the remaining valid channels.

---

# Code Organization

Follow the existing project architecture.

- Keep `server.py` responsible for Discord event handling.
- Reuse the existing issue extraction service.
- Reuse the existing database repository/service.
- Avoid duplicating business logic.

---

# Acceptance Criteria

- The bot listens for new Discord messages using the existing event system.
- Only messages from channels configured in `.env` are processed.
- Messages from other channels are ignored.
- Existing MCP functionality remains unchanged.
- Errors in one message do not affect processing of subsequent messages.
- Logging clearly indicates whether a message was processed or ignored.
- The implementation follows the existing project structure and coding conventions.