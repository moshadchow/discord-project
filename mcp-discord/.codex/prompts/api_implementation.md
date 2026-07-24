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

## Request

```json
{
    "discord_message_id": "123456789",
    "message": "Issue has been resolved."
}
```

## Processing Steps

1. Look up the issue using `discord_message_id`.
2. Retrieve the associated `channel_id`.
3. Reuse the project's existing Discord message sending implementation.
4. **Do NOT** duplicate Discord client logic.
5. Send the supplied message to the corresponding Discord channel.

## Success Response

```json
{
    "success": true,
    "channel_id": "...",
    "discord_message_id": "...",
    "message_sent": true
}
```

## Error Handling

Return:

- **404** if the issue is not found.
- **500** if Discord message delivery fails.

---

# Dependency Injection

Create reusable dependencies.

```python
get_session()

get_issue_repository()

get_issue_service()
```

Use FastAPI dependency injection throughout the project.

---

# Request & Response Schemas

Create:

```
schemas/issues.py
```

Include:

- ReplyRequest
- IssueResponse
- IssueListResponse
- ApiResponse

Use SQLModel/Pydantic models for validation.

---

# Error Handling

Return consistent API responses.

Example:

```json
{
    "success": false,
    "message": "Issue not found"
}
```

Requirements:

- Never expose stack traces.
- Return appropriate HTTP status codes.
- Use meaningful error messages.

---

# Logging

Use the project's existing logging framework.

Log:

- Incoming requests
- Database exceptions
- Discord send failures
- Unexpected exceptions

Avoid logging sensitive information.

---

# Testing

Create unit tests for:

- Repository
- Service
- FastAPI endpoints

Requirements:

- Mock database interactions.
- Mock Discord interactions.
- Use Python's `unittest` framework.
- Follow existing project testing conventions.

---

# Code Quality

Follow the project's coding standards.

## General

- Follow PEP-8.
- Use Python type hints everywhere.
- Add docstrings.
- Keep functions small and focused.
- Avoid duplicated code.
- Keep business logic inside the service layer.

## Architecture

Maintain clear separation between:

```
API
    ↓
Service
    ↓
Repository
    ↓
SQLModel
```

Do not place database logic inside the API layer.

Do not place business logic inside the repository.

---

# Existing Discord Integration

Reuse the project's existing Discord utilities.

Do **NOT**:

- Create another Discord client.
- Duplicate message sending logic.
- Modify existing MCP tools.
- Break existing Discord functionality.

---

# Deliverables

Implement the following new modules:

```
models/
    issue.py

repositories/
    issues_repository.py

services/
    issues_service.py

schemas/
    issues.py

api/
    issues.py
```

Ensure the API is fully integrated into the existing FastAPI application.

---

# Expected Outcome

The completed implementation should provide:

- Fetch issue by `discord_message_id`
- Fetch issues by `channel_id`
- Fetch issues by `sender`
- Send a reply to the original Discord channel using `discord_message_id`
- Production-ready architecture
- Clean separation of concerns
- Fully typed SQLModel implementation
- Comprehensive error handling
- Logging
- Unit tests
- No regression to existing MCP functionality