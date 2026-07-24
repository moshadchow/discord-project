# Add a New MCP Tool: `reply_message`

Extend the existing Discord MCP server by adding a new MCP tool named `reply_message`.

Follow **ALL** coding conventions and architecture defined in **AGENTS.md**.

---

# Objective

Implement a new MCP tool that replies directly to an existing Discord message using its `discord_message_id`.

This tool will be used by the FastAPI backend instead of sending a normal channel message, allowing replies to remain threaded with the original issue.

---

# Existing Project

The project already contains:

- Discord bot setup
- MCP server
- `call_tool()` dispatcher
- Existing message tools such as:
  - `send_message`
  - `read_messages`
  - `moderate_message`
  - `add_reaction`
  - `remove_reaction`

The new tool must follow the same implementation pattern.

---

# Location

Modify:

```
src/discord_mcp/server.py
```

---

# New MCP Tool

Add a new tool under the **Message Reaction Tools** section.

Tool name:

```
reply_message
```

---

# Tool Signature

```python
reply_message(
    channel_id: str,
    discord_message_id: str,
    message: str
)
```

Parameters:

| Parameter | Description |
|----------|-------------|
| channel_id | Discord channel containing the original message |
| discord_message_id | Discord message ID to reply to |
| message | Reply message |

---

# Behavior

The tool should:

1. Validate the input parameters.
2. Retrieve the Discord channel using `channel_id`.
3. Fetch the original message using `discord_message_id`.
4. Reply to that message using Discord.py's native reply functionality.
5. Return the newly created reply message information.

The reply should appear as a threaded reply beneath the original Discord message.

Do **NOT** send a normal channel message.

---

# Return Value

Return a structured response similar to existing MCP tools.

Example:

```json
{
    "success": true,
    "message_id": "987654321098765432",
    "channel_id": "123456789012345678",
    "reply_to_message_id": "111111111111111111",
    "timestamp": "2026-07-24T10:15:30Z"
}
```

---

# Error Handling

Return meaningful errors for:

- Invalid channel
- Message not found
- Missing permissions
- Discord API errors
- Unexpected exceptions

Do not expose stack traces.

---

# Logging

Log:

- Reply request received
- Channel lookup
- Original message lookup
- Reply sent successfully
- Discord API failures
- Unexpected exceptions

Follow the project's existing logging approach.

---

# Integration with MCP

Register the tool in the same way as the existing Message Operations tools.

Update:

- MCP tool registration
- Tool metadata
- `call_tool()` dispatcher

Ensure the tool is discoverable by MCP clients.

---

# Documentation

Update the Message Reaction Tools section to include:

```
reply_message
```

Description:

> Reply to an existing Discord message using its `discord_message_id`.

---

# Testing

Add unit tests covering:

- Successful reply
- Invalid channel
- Invalid message ID
- Missing permissions
- Discord API exception
- Unexpected exception

Mock all Discord interactions.

Use Python's `unittest` framework.

---

# Code Quality

- Follow PEP-8.
- Use Python type hints.
- Add docstrings.
- Keep functions small and focused.
- Reuse existing Discord client and helper methods.
- Do **NOT** duplicate existing message sending logic.
- Maintain consistency with the existing MCP tool implementations.

---

# Deliverables

Update the following components:

```
src/
└── discord_mcp/
    └── server.py
```

The implementation should include:

- New MCP tool: `reply_message`
- Tool registration
- `call_tool()` dispatch support
- Structured response
- Error handling
- Logging
- Unit tests
- Updated documentation

The new tool should seamlessly integrate with the existing Discord MCP server and follow the project's established architecture and coding conventions.