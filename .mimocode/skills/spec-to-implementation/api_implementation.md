# FastAPI Issue Management API Implementation

You are an expert Python backend developer specializing in **FastAPI**, **SQLModel**, and **clean architecture**.

Your task is to extend this project by implementing a REST API layer for querying the existing PostgreSQL `issues` table and sending Discord messages.

---

# Requirements

Follow **ALL** coding conventions and architecture defined in **AGENTS.md**.

## Existing Project

- Language: Python 3.10+
- Framework: FastAPI
- ORM: SQLModel
- Database: PostgreSQL
- Discord integration already exists through MCP tools.
- Existing project structure should be respected.
- Reuse the existing database configuration.
- Reuse the existing Discord messaging functionality instead of creating duplicate logic.
- Follow dependency injection and repository pattern where appropriate.
- Add proper type hints.
- Add docstrings.
- Return proper HTTP status codes.
- Handle errors gracefully.

---

# Database

Use **SQLModel** to map the existing `issues` table.

The table already exists and contains fields including:

| Column |
|---------|
| id |
| discord_message_id |
| guild_id |
| guild_name |
| channel_id |
| channel_name |
| sender |
| issue_date |
| issue_time |
| issue |
| attachments |
| message_timestamp |
| message_timestamp_local |
| created_at |
| updated_at |

> **Important:** Do **NOT** recreate the table.

---

# 1. SQLModel

Create:

```
models/issue.py
```

Define a SQLModel model that maps to the existing `issues` table.

---

# 2. Repository Layer

Create:

```
repositories/issues_repository.py
```

Implement the following methods:

```python
get_by_discord_message_id(discord_message_id: str)

get_by_channel_id(channel_id: str)

get_by_sender(sender: str)
```

### Requirements

- Use SQLModel queries.
- Return SQLModel objects.
- Raise appropriate exceptions when needed.
- Keep repository free from business logic.

---

# 3. Service Layer

Create:

```
services/issues_service.py
```

Business logic should wrap repository calls.

Implement:

```python
get_issue_by_message_id()

get_issues_by_channel()

get_issues_by_sender()
```

Responsibilities:

- Validate input
- Handle business rules
- Raise meaningful exceptions
- Keep API layer thin

---

# 4. API Layer

Create:

```
api/issues.py
```

Implement the following REST endpoints.

---

## Endpoint 1

### Fetch Issue by Discord Message ID

```
GET /api/issues/message/{discord_message_id}
```

### Success Response

```json
{
    "success": true,
    "data": {
        ...
    }
}
```

### Error

Return **404** if the issue does not exist.

---

## Endpoint 2

### Fetch Issues by Channel

```
GET /api/issues/channel/{channel_id}
```

### Success Response

```json
{
    "success": true,
    "count": 15,
    "data": [
        ...
    ]
}
```

---

## Endpoint 3

### Fetch Issues by Sender

```
GET /api/issues/sender/{sender}
```

Support optional query parameters:

```
skip
limit
```

Example:

```
GET /api/issues/sender/john?skip=0&limit=20
```

---

# 5. Reply to a Discord Issue

Implement:

```
POST /api/issues/reply
```

## Purpose

Reply to an existing Discord issue by locating the original issue via its `discord_message_id`, sending a message to the same Discord channel by locating the original `discord_message_id`, and recording the reply in the `issues` table to maintain a complete conversation history.

---

## Request

```json
{
    "discord_message_id": "123456789",
    "message": "Issue has been resolved."
}
```

---

## Processing Steps

1. Look up the issue using `discord_message_id`.
2. If the issue does not exist, return **404**.
3. Retrieve the original issue details:
   - `guild_id`
   - `guild_name`
   - `channel_id`
   - `channel_name`
   - `sender`
4. Reuse the project's existing Discord message sending implementation.
5. **Do NOT** duplicate Discord client logic.
6. Send the supplied message to the corresponding Discord channel.
7. Capture the Discord response and retrieve the newly created Discord message information (at minimum the new `discord_message_id` and `message_timestamp`).
8. Persist the sent message as a **new record** in the `issues` table.
9. Return the newly created record information.

---

## Database Insert

After successfully sending the message, insert a new row into the existing `issues` table.

Populate the fields as follows:

| Column | Value |
|---------|-------|
| discord_message_id | Newly created Discord message ID returned by Discord |
| guild_id | Original issue's guild_id |
| guild_name | Original issue's guild_name |
| channel_id | Original issue's channel_id |
| channel_name | Original issue's channel_name |
| sender | Configurable application sender (e.g. `SYSTEM`, `BOT`, or configured bot username) |
| issue_date | Date of the sent reply |
| issue_time | Time of the sent reply |
| issue | Reply message text |
| attachments | Empty JSON array (`[]`) unless attachments are included |
| message_timestamp | Timestamp returned by Discord |
| message_timestamp_local | Converted local timestamp |
| created_at | Auto-generated |
| updated_at | Auto-generated |

> **Important:** The reply must be stored as a **new record**. Never update or overwrite the original issue.

---

## Repository Layer

Add a repository method:

```python
create_issue(issue: IssueCreate) -> Issue
```

This method is responsible only for inserting the new record.

---

## Service Layer

Add:

```python
reply_to_issue(
    discord_message_id: str,
    message: str
)
```

Responsibilities:

- Retrieve the original issue.
- Send the reply using the existing Discord messaging implementation.
- Build a new Issue model using the Discord response.
- Insert the new issue record into the database.
- Return the persisted record.

The service should guarantee transactional consistency:

- If the Discord message fails, **do not** insert into the database.
- If the database insert fails after Discord succeeds, log the error and return an appropriate error response.

---

## Success Response

```json
{
    "success": true,
    "message_sent": true,
    "data": {
        "id": 1054,
        "discord_message_id": "987654321098765432",
        "channel_id": "123456789012345678",
        "sender": "SYSTEM",
        "issue": "Issue has been resolved.",
        "message_timestamp": "2026-07-24T10:30:15Z"
    }
}
```

---

## Error Responses

### Issue Not Found

```json
{
    "success": false,
    "message": "Issue not found"
}
```

HTTP Status: **404**

---

### Discord Send Failed

```json
{
    "success": false,
    "message": "Failed to send Discord message"
}
```

HTTP Status: **500**

---

### Database Insert Failed

```json
{
    "success": false,
    "message": "Discord message sent but failed to persist reply."
}
```

HTTP Status: **500**

---

## Logging

Log the following events:

- Reply request received
- Original issue found
- Discord message sent successfully
- Database insert successful
- Discord send failure
- Database insert failure
- Unexpected exceptions

---

## Testing

Add unit tests covering:

- Successful reply and database insert
- Original issue not found
- Discord send failure
- Database insert failure
- Validation errors

Mock both the repository and the existing Discord messaging implementation.

> **Important:** Always reuse the project's existing `send_message` implementation. Do **NOT** create another Discord client or duplicate the Discord messaging logic. The newly sent Discord message **must** be persisted as a new record in the `issues` table after a successful send.
---

# 6. Remove Discord Issue Message

Implement:

```
DELETE /api/issues/message/{discord_message_id}
```

## Purpose

Remove the original Discord issue message using the project's existing `moderate_message` implementation and, upon successful deletion, remove the corresponding record from the `issues` table to keep Discord and the database synchronized.

---

## Processing Steps

1. Look up the issue using `discord_message_id`.
2. If the issue does not exist, return **404**.
3. Retrieve the associated:
   - `guild_id`
   - `channel_id`
   - `discord_message_id`
4. Reuse the project's existing `moderate_message` implementation.
5. **Do NOT** create a new Discord client or duplicate moderation logic.
6. Delete the Discord message.
7. If the Discord message is successfully deleted, remove the corresponding record from the `issues` table using the same `discord_message_id`.
8. Return success only if **both** the Discord message deletion and the database deletion succeed.

> **Important:** The database record must only be deleted **after** the Discord message has been successfully removed. If the Discord deletion fails, the database record must remain unchanged.

---

## Repository Layer

No additional lookup methods are required beyond:

```python
get_by_discord_message_id(discord_message_id: str)
```

Add a new repository method:

```python
delete_by_discord_message_id(discord_message_id: str) -> bool
```

Responsibilities:

- Delete the record matching the specified `discord_message_id`.
- Return `True` if a record was deleted.
- Return `False` if no matching record exists.

---

## Service Layer

Add:

```python
delete_issue_message(discord_message_id: str)
```

Responsibilities:

- Retrieve the issue from the repository.
- Validate that the issue exists.
- Invoke the existing `moderate_message` implementation to delete the Discord message.
- If the Discord deletion succeeds, delete the corresponding record from the `issues` table.
- Handle Discord and database exceptions.
- Return a structured response.

---

## Success Response

```json
{
    "success": true,
    "discord_message_id": "123456789",
    "channel_id": "987654321",
    "message_deleted": true,
    "database_record_deleted": true
}
```

---

## Error Responses

### Issue Not Found

```json
{
    "success": false,
    "message": "Issue not found"
}
```

**HTTP Status:** `404`

---

### Discord Deletion Failed

```json
{
    "success": false,
    "message": "Failed to delete Discord message"
}
```

**HTTP Status:** `500`

> In this case, **do not** remove the database record.

---

### Database Deletion Failed

```json
{
    "success": false,
    "message": "Discord message deleted, but failed to remove the corresponding database record."
}
```

**HTTP Status:** `500`

> The Discord message has already been deleted. Log the database failure for manual reconciliation.

---

## Logging

Log the following events:

- Delete request received
- Issue found
- Discord message deletion started
- Discord message deleted successfully
- Database record deletion started
- Database record deleted successfully
- Discord deletion failure
- Database deletion failure
- Discord deletion succeeded but database cleanup failed
- Unexpected exceptions

---

## Testing

Add unit tests covering:

- Successful Discord deletion and database deletion
- Unknown `discord_message_id`
- Discord deletion failure (database record remains unchanged)
- Database deletion failure after successful Discord deletion
- Repository failure
- Discord API exceptions

Mock both the repository and the existing `moderate_message` implementation.

---

## Important Requirements

- Always reuse the project's existing `moderate_message` implementation.
- Do **NOT** create a new Discord client.
- Do **NOT** duplicate Discord moderation logic.
- Keep Discord and the database synchronized by deleting the database record only after successful Discord message deletion.
- Preserve the existing project architecture (API → Service → Repository → SQLModel).
```