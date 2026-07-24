# Repository Guidelines

## Project Structure & Module Organization

This repository is a Python MCP server package for Discord. Source code lives in `src/discord_mcp/`. The main server, Discord bot setup, MCP tool registration, event handlers, and `call_tool()` dispatch are in `server.py`. Package startup logic is in `__init__.py`, including Windows event loop setup.

Issue capture is split across focused modules: `issue_parser.py` extracts issue fields, `issue_capture.py` converts Discord messages into `IssueRecord` objects and reports capture status, `issues_repository.py` owns PostgreSQL schema/insert behavior (writes only via psycopg), and `config.py` loads database, monitored-channel, and authentication settings. `seed.py` is a standalone historical backfill script that reuses the same parser, capture service, and repository.

### Core Module (`core/`)

Shared security utilities used by the authentication system:

| Module | Responsibility |
|--------|---------------|
| `core/__init__.py` | Empty package |
| `core/security.py` | Password hashing with bcrypt (`hash_password()`, `verify_password()`) |
| `core/jwt.py` | JWT token creation and verification (`create_access_token()`, `decode_access_token()`) |

### REST API Module (`api/`)

A FastAPI REST API layer runs concurrently with the MCP server when `DATABASE_URL` is configured. It provides access to the issues table, reply endpoint, and user authentication. The API communicates with Discord exclusively through the MCP tools via a gateway abstraction — no direct `discord.py` usage exists in the API layer.

```
API (routes) → Service → DiscordGateway → MCP Tools → Discord.py
                                                      ↓
                                              Repository → SQLModel
```

| Module | Responsibility |
|--------|---------------|
| `api/__init__.py` | FastAPI app factory (`create_app()`) with startup lifespan that auto-creates the `users` table |
| `api/models.py` | SQLModel `IssueRow` and `UserRow` table mappings |
| `api/schemas.py` | Pydantic request/response models |
| `api/mcp_models.py` | Pydantic models for MCP tool JSON responses (`ReplyMessageResult`, `DeleteMessageResult`) |
| `api/repository.py` | `IssueRepository` and `UserRepository` (SQLModel queries, `UserRepository.ensure_users_table()` for schema init) |
| `api/service.py` | `IssueQueryService` and `AuthService` — business logic, no Discord.py imports |
| `api/discord_gateway.py` | `DiscordGateway` — translates service requests into MCP tool calls |
| `api/deps.py` | FastAPI DI providers (session, repo, service, gateway, auth) |
| `api/routes.py` | API endpoint handlers (issues + authentication) |

The API uses its own `AsyncEngine` (via `create_async_engine` + asyncpg) separate from the existing psycopg `AsyncConnectionPool` used for writes. Both connect to the same PostgreSQL database. On startup, a FastAPI lifespan creates the `users` table if it doesn't exist.

Tests live in `tests/` and use Python `unittest`. Current tests cover config parsing, issue parsing, issue capture, seed helpers, security utilities, authentication service/routes, and the API layer (repository, service, and endpoint tests). `mcp_client.py` is a sample stdio client and test harness, not the primary application. Runtime and packaging metadata are in `pyproject.toml`, `requirements.txt`, `uv.lock`, `Dockerfile`, and `smithery.yaml`.

## MCP Tools

The server exposes the following MCP tools for Discord operations:

**Server Information:**
- `get_server_info`: Get information about a Discord server
- `get_channels`: Get a list of all channels in a Discord server
- `list_servers`: Get a list of all Discord servers the bot has access to

**User Management:**
- `list_members`: Get a list of members in a server
- `get_user_info`: Get information about a Discord user

**Role Management:**
- `add_role`: Add a role to a user
- `remove_role`: Remove a role from a user

**Channel Management:**
- `create_text_channel`: Create a new text channel
- `delete_channel`: Delete a channel

**Message Operations:**
- `send_message`: Send a message to a specific channel
- `read_messages`: Read recent messages from a channel
- `moderate_message`: Delete a message and optionally timeout the user
- `reply_message`: Reply to an existing Discord message using its `discord_message_id`

**Reactions:**
- `add_reaction`: Add a reaction to a message
- `add_multiple_reactions`: Add multiple reactions to a message
- `remove_reaction`: Remove a reaction from a message

## REST API Endpoints

When `DATABASE_URL` is configured, a FastAPI server starts on port 8000 alongside the MCP server. Swagger docs at `/api/docs`.

### Issue Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/issues/message/{discord_message_id}` | Fetch issue by Discord message ID (404 if not found) |
| GET | `/api/issues/channel/{channel_id}` | Fetch all issues for a channel |
| GET | `/api/issues/sender/{sender}?skip=0&limit=50` | Fetch issues by sender with pagination |
| POST | `/api/issues/reply` | Send a reply to the original Discord channel (body: `discord_message_id`, `message`) |
| DELETE | `/api/issues/message/{discord_message_id}` | Delete the original Discord issue message (404 if not found) |

### Authentication Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/login` | Authenticate user and return JWT access token (body: `username`, `password`) |
| POST | `/api/auth/logout` | Log out (stateless — client removes token) |
| GET | `/api/auth/profile` | Get current authenticated user profile (requires Bearer token) |

Protected endpoints use `OAuth2PasswordBearer` with `tokenUrl="/api/auth/login"`. Include `Authorization: Bearer <token>` header for authenticated requests.

## Build, Test, and Development Commands

- `uv venv`: create a local virtual environment.
- `.\.venv\Scripts\activate`: activate the environment on Windows.
- `uv pip install -e .`: install the package in editable mode.
- `uv run mcp-discord`: run the MCP server console entry point.
- `python -m discord_mcp`: run through the package entry point.
- `.\.venv\Scripts\python.exe -m unittest discover`: run the test suite with the local virtual environment on Windows.
- `.\.venv\Scripts\python.exe -m compileall src tests seed.py`: check Python syntax across source, tests, and the seed script.
- `python seed.py --channel "support-issues"`: backfill historical issues from a Discord channel after installing dependencies and setting required environment variables.
- `python seed.py --channel "support-issues" --from-date 2024-01-01 --to-date 2024-01-31`: backfill issues from a specific date range.
- `python seed.py --channel "support-issues" --limit 100`: backfill up to 100 historical issues.

## Coding Style & Naming Conventions

Use Python 3.10+ syntax, four-space indentation, and clear snake_case names for functions, variables, and modules. Keep Discord event wiring and MCP tool dispatch in `server.py`; put parsing, persistence, and configuration logic in their dedicated modules. Prefer typed dataclasses for structured records, as in `IssueRecord`, `ExtractedIssue`, `IssueCaptureResult`, `MonitoredChannelsConfig`, and `AuthConfig`.

Do not import `discord_mcp.server` from scripts or tests that only need shared logic; it performs Discord/MCP setup at import time. Reuse `IssueCaptureService`, `IssuesRepository`, `AuthService`, `UserRepository`, and config helpers directly instead of duplicating extraction, duplicate handling, or database insert logic.

### Data Classes

- `IssueRecord`: Represents a captured Discord message with issue details (discord_message_id, guild_id, guild_name, channel_id, channel_name, sender, issue_date, issue_time, issue, message_timestamp, message_timestamp_local, attachments)
- `ExtractedIssue`: Parsed issue data from message content (issue_date, issue_time, sender, issue)
- `IssueCaptureResult`: Result of capture operation with status and message ID
- `IssueAttachment`: File attachment metadata (attachment_name, original_file_name, file_extension, url, content_type, size_bytes)
- `DatabaseConfig`: PostgreSQL configuration (database_url, capture_enabled property)
- `MonitoredChannelsConfig`: Channel filtering (channel_ids, channel_names, enabled property, matches_channel method)
- `AuthConfig`: JWT authentication settings (jwt_secret_key, jwt_algorithm, jwt_access_token_expire_minutes)
- `SeedOptions`: Backfill command arguments (channel, limit, from_date, to_date)

### API Models (Pydantic/SQLModel)

- `IssueRow` (SQLModel): Table mapping to existing `issues` table (api/models.py)
- `UserRow` (SQLModel): Table mapping to `users` table (api/models.py)
- `IssueResponse`: Single issue in API responses (api/schemas.py)
- `IssueListResponse`: Paginated list of issues with count (api/schemas.py)
- `IssueAttachmentResponse`: Attachment metadata in API responses (api/schemas.py)
- `ReplyRequest`: Request body for sending a Discord reply (api/schemas.py)
- `ReplyResponse`: Response after sending a Discord reply (api/schemas.py)
- `ErrorResponse`: Standard error response (api/schemas.py)
- `LoginRequest`: Request body for user login (api/schemas.py)
- `LoginResponse`: Response after successful login with JWT token (api/schemas.py)
- `LogoutResponse`: Response after logout (api/schemas.py)
- `UserSummary`: Minimal user info in API responses (api/schemas.py)

### MCP Response Models (api/mcp_models.py)

- `ReplyMessageResult`: Parsed response from the `reply_message` MCP tool (success, message_id, reply_to_message_id, channel_id, timestamp)
- `DeleteMessageResult`: Parsed response from the `moderate_message` MCP tool (success, message_id, channel_id, message_deleted, timed_out)

### Enums

- `IssueCaptureStatus`: Capture states (DISABLED, INSERTED, DUPLICATE, EXTRACTION_FAILED, DATABASE_FAILED, DELETED)

## Testing Guidelines

Use `unittest` and name test files `test_*.py`. Keep parser tests deterministic with fixed timestamps. For async behavior, use `unittest.IsolatedAsyncioTestCase` and fake repositories or fake Discord-like objects instead of live Discord or PostgreSQL connections.

Add or update tests when changing issue extraction, duplicate handling, monitored-channel filtering, seed argument parsing/history ordering, MCP tool behavior, or authentication logic. Keep environment-variable tests isolated with `unittest.mock.patch.dict` so local `.env` values do not affect results.

### API Tests

API tests use the same patterns: `FakeRepository` classes for repository/service tests and `FastAPI TestClient` with dependency overrides for endpoint tests. Never connect to a real database or Discord in tests.

Service tests mock `DiscordGateway` (not the Discord client directly). The gateway abstraction ensures the service layer has no knowledge of `discord.py` internals.

### Authentication Tests

Auth tests follow the same patterns: `FakeUserRow` for model stand-ins, `FakeUserRepository` for in-memory repository, and `TestClient` with `dependency_overrides` for endpoint tests. JWT creation/verification is tested with mocked config to avoid hardcoding secrets. Password hashing tests use real bcrypt (no mocking needed).

## Commit & Pull Request Guidelines

Follow the existing history: short imperative subjects such as `Add list_servers tool`, with `fix:` prefixes acceptable for bug fixes. Pull requests should describe behavior changes, list validation commands run, and mention any new environment variables or Discord permissions. Do not include screenshots unless a user-facing UI is added.

## Security & Configuration Tips

Never commit Discord tokens, real channel IDs, database credentials, or JWT secret keys. The server and `seed.py` load `.env` automatically, but shell or MCP client environment variables take precedence. `DISCORD_TOKEN` is required to run the bot or seed script.

`DATABASE_URL` enables PostgreSQL issue capture, schema creation, and user authentication. `DISCORD_MONITORED_CHANNEL_IDS` and `DISCORD_MONITORED_CHANNELS` restrict automatic capture to configured channels; prefer IDs because names can change. If no monitored channels are configured, automatic issue capture ignores incoming messages while MCP tools continue to run.

### Environment Variables

- `DISCORD_TOKEN`: Required. The Discord bot token for authentication.
- `DATABASE_URL`: Optional. PostgreSQL connection string for issue capture and authentication. When set, the server automatically creates the `issues` and `users` tables if they don't exist.
- `DISCORD_MONITORED_CHANNEL_IDS`: Optional. Comma-separated list of Discord channel IDs to monitor for issues.
- `DISCORD_MONITORED_CHANNELS`: Optional. Comma-separated list of Discord channel names to monitor for issues.
- `JWT_SECRET_KEY`: Required for authentication. Secret key used to sign JWT tokens. Change in production.
- `JWT_ALGORITHM`: Optional. JWT signing algorithm (default: `HS256`).
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: Optional. Token expiration in minutes (default: `1440` = 24 hours).

### Database Schema

When `DATABASE_URL` is configured, the server creates the following tables:

**issues table:**
- `id`: BigSerial primary key
- `discord_message_id`: Unique identifier from Discord (TEXT, UNIQUE NOT NULL)
- `guild_id`, `guild_name`: Discord server information (TEXT, nullable)
- `channel_id`, `channel_name`: Discord channel information (TEXT, channel_id NOT NULL)
- `sender`: Message author (TEXT, NOT NULL)
- `issue_date`, `issue_time`: Extracted date and time (DATE/TIME, NOT NULL)
- `issue`: Full message content (TEXT, NOT NULL)
- `attachments`: JSON array of file attachment metadata (JSONB, default '[]')
- `message_timestamp`, `message_timestamp_local`: Original and local timestamps (TIMESTAMPTZ/TIMESTAMP, NOT NULL)
- `created_at`, `updated_at`: Record timestamps (TIMESTAMPTZ, default now())

**users table:**
- `id`: BigSerial primary key
- `username`: Unique username (VARCHAR(100), UNIQUE NOT NULL)
- `password_hash`: Bcrypt hashed password (TEXT NOT NULL)
- `full_name`: User's full name (VARCHAR(200) NOT NULL)
- `email`: Optional unique email (VARCHAR(255), UNIQUE)
- `role`: User role (VARCHAR(50), default 'User')
- `is_active`: Whether the account is active (BOOLEAN, default true)
- `last_login_at`: Last successful login timestamp (TIMESTAMPTZ, nullable)
- `created_at`, `updated_at`: Record timestamps (TIMESTAMPTZ, default now())
