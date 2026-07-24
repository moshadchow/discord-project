# Feature Enhancement: Capture Discord Issues and Persist to PostgreSQL

Implement a new feature in the Discord MCP server to automatically capture issue-related messages from Discord and persist them to a PostgreSQL database.

## Objective

Whenever a new message is received from a Discord channel that the bot has access to, automatically extract the issue information from the message and save it to PostgreSQL.

This feature should operate transparently without affecting the existing MCP tool functionality.

---

## Implementation Requirements

### 1. Message Listener

Enhance the Discord bot to listen for new messages using the existing Discord event system (e.g., `on_message`).

Requirements:

* Process every newly received message after the bot is fully connected (`on_ready`).
* Ignore messages sent by the bot itself.
* Continue processing existing MCP functionality without interruption.

---

### 2. Issue Extraction

For each new message, extract the following information:

| Field        | Description                                                                                     |
| ------------ | ----------------------------------------------------------------------------------------------- |
| `issue_date` | Date extracted from the message. If no explicit date exists, use the Discord message timestamp. |
| `issue_time` | Time extracted from the message. If no explicit time exists, use the Discord message timestamp. |
| `sender`     | Discord username or display name of the message author.                                         |
| `issue`      | The issue description extracted from the message body.                                          |

Additional metadata (recommended):

* Discord Message ID
* Channel ID
* Channel Name
* Server (Guild) ID
* Server Name
* Message Timestamp (UTC)
* Message Timestamp (Local)
* Created At
* Updated At

---

### 3. Database Persistence

Save the extracted information into a PostgreSQL table.

Suggested schema:

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
created_at
updated_at
```

Requirements:

* Use the project's existing PostgreSQL connection and ORM/database layer.
* Use parameterized queries or ORM methods.
* Wrap inserts in transactions where appropriate.

---

### 4. Duplicate Prevention

Prevent duplicate issue records.

Use the Discord Message ID as the primary uniqueness check.

If a message has already been processed:

* Skip the insert.
* Log that the message already exists.
* Do not generate an error.

---

### 5. Error Handling

The feature should never interrupt the Discord bot.

If extraction or database persistence fails:

* Log the error.
* Continue processing subsequent messages.
* Do not crash the MCP server.

---

### 6. Logging

Add structured logging for:

* New message received
* Issue successfully extracted
* Database insert successful
* Duplicate message detected
* Extraction failure
* Database failure

Do not log sensitive information.

---

### 7. Code Organization

Implement the feature following the existing project architecture.

Recommended separation of responsibilities:

* Discord message listener
* Issue extraction/parser
* Database repository/service
* PostgreSQL model/entity
* Configuration
* Logging

Keep `server.py` focused on Discord event handling and delegate business logic to dedicated modules where appropriate.

---

### 8. Configuration

Use the existing environment/configuration mechanism for PostgreSQL connectivity.

Do not hardcode:

* Database host
* Username
* Password
* Database name
* Port

---

### 9. Documentation

Update `AGENTS.md` and `README.md` only if configuration or usage changes are introduced.

Document:

* Required PostgreSQL configuration
* Database schema (if applicable)
* Any new runtime dependencies

---

## Acceptance Criteria

* Every new Discord message is processed automatically.
* The issue date, time, sender, and issue description are extracted correctly.
* Each message is stored only once using the Discord Message ID as the unique identifier.
* Existing MCP tools continue to function without regression.
* The bot remains stable even if extraction or database operations fail.
* The implementation follows the existing project structure and coding conventions.
