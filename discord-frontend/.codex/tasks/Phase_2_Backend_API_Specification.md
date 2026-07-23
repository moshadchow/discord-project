# Phase 2 Backend REST API Implementation Plan

  ## Summary

  Extend mcp-discord with a FastAPI REST API that runs in the same process as the existing Discord bot and MCP stdio server. The API will reuse the existing
  bot instance for Discord replies and extend IssuesRepository for issue listing, status updates, notes, replies, dashboard summaries, and database-backed
  admin authentication.

  ## Key Changes

  - Add REST dependencies to mcp-discord: fastapi, uvicorn, pydantic, python-jose or equivalent JWT library, passlib[bcrypt].
  - Add API modules under src/discord_mcp/, keeping server.py responsible for wiring bot/MCP/API runtime.
  - Start uvicorn as an async task inside the existing main() so the Discord bot, MCP server, and REST API share process state.
  - Add config values:
      - API_HOST, API_PORT
      - JWT_SECRET_KEY, JWT_ACCESS_TOKEN_MINUTES, JWT_REFRESH_TOKEN_DAYS
      - CORS_ORIGINS
      - one-time bootstrap envs for first admin creation, e.g. ADMIN_BOOTSTRAP_USERNAME, ADMIN_BOOTSTRAP_PASSWORD, ADMIN_BOOTSTRAP_USER_ID

  ## Database And Repository

  - Extend schema creation/migrations to include:
      - issues.status TEXT NOT NULL DEFAULT 'Pending'
      - existing audit tables: issue_status_history, issue_notes, issue_replies
      - new auth tables: admin_users, refresh_tokens

  - admin_users stores username, password hash, role, active flag, created/updated timestamps.
  - refresh_tokens stores token hash, admin user id, expiry, revoked timestamp, created timestamp.
  - Add repository methods for:
      - admin lookup, password verification support, refresh token create/revoke/lookup
      - channel summaries with unresolved counts and last activity
      - issue search/filter by channel, status, sender, date range, and text query
      - issue detail with attachments, notes, replies, and current status
      - status update in one transaction: update issues.status, insert issue_status_history
      - notes insert/list
      - replies insert/list after Discord send succeeds
      - dashboard aggregate counts

  ## REST API Behavior

  - POST /auth/login
      - Validate username/password.
      - Return access token, refresh token, admin user id, username, role.
      - Log login success/failure with structured metadata.

  - POST /auth/refresh
      - Validate non-revoked refresh token.
      - Return new access token.

  - POST /auth/logout
      - Revoke the presented refresh token.

  - All non-auth endpoints require Bearer JWT.
  - All mutation endpoints require role = admin.
  - GET /channels
      - Return channel_id, channel_name, unresolved issue count where status is not Solved, and last activity timestamp.

  - GET /issues
      - Return filtered issue list with current status, attachments metadata, last updated, notes/reply counts.

  - GET /issues/{id}
      - Return full issue record, attachments, notes, replies, and status history.

  - PATCH /issues/{id}/status
      - Accept only Pending, Solved, Need Clarification.
      - Store previous and new status in issue_status_history.

  - GET /issues/{id}/notes
      - Return notes chronologically.

  - POST /issues/{id}/notes
      - Store plain text note with authenticated admin user id.

  - GET /issues/{id}/replies
      - Return reply history chronologically.

  - POST /issues/{id}/reply
      - Fetch issue channel from DB.
      - Use the existing in-memory Discord bot to send the reply.
      - Persist reply with admin user id, reply date, reply time, and Discord message id.

  - GET /dashboard/summary
      - Return total issues, counts by status, today’s issues, and total channels.

  ## Validation And Errors

  - Use Pydantic request/response models for every endpoint.
  - Return consistent JSON errors:
      - 401 invalid/expired token
      - 403 non-admin mutation attempt
      - 404 issue/admin resource not found
      - 422 validation errors
      - 502 Discord send failure
      - 500 unexpected database/runtime failure

  - Add structured logs for login, logout, validation failure, status update, notes, replies, Discord failure, and database failure.

  ## Test Plan

  - Add unittest coverage with fake repositories and fake Discord bot/channel objects.
  - Test auth:
      - login success/failure
      - refresh success/revoked/expired
      - logout revokes refresh token
      - non-admin mutation returns 403

  - Test API behavior:
      - channel summary aggregation
      - issue filters combine correctly
      - issue detail includes attachments, notes, replies, status history
      - status update writes both current status and history
      - note creation stores admin id
      - reply endpoint sends through existing bot and persists Discord message id
      - Discord failure does not persist reply
      - dashboard counts match statuses

  - Run:
      - python -m unittest discover
      - python -m compileall src tests seed.py

  ## Assumptions

  - Admin authentication is database-backed, per user selection.
  - REST API runs in the same process as the existing MCP server and Discord bot, per user selection.
  - Pending is the default status for all existing and newly captured issues.
  - Refresh tokens are persisted as hashes, not raw tokens.
  - The first admin can be bootstrapped from environment variables when no admin user exists.
  - Existing MCP tools and issue capture behavior must keep working unchanged.
