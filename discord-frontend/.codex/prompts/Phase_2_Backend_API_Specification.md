# Phase 2 --- Backend API Specification (Extend `discord-mcp`)

## Objective

Extend the existing `mcp-discord` backend to provide secure REST APIs
for authentication, channel management, issue management, notes,
replies, and dashboard summaries while reusing the existing Discord bot
connection and repository layer.

## Authentication

### POST /auth/login

-   Authenticate administrator
-   Return JWT access token and refresh token

### POST /auth/refresh

-   Refresh access token

### POST /auth/logout

-   Invalidate refresh token

### Authorization

-   JWT authentication
-   Role-based authorization
-   Admin role required for all mutation endpoints

## Channels

### GET /channels

Return:

-   Channel ID
-   Channel Name
-   Unresolved Issue Count
-   Last Activity

## Issues

### GET /issues

Support filters:

-   channel
-   status
-   sender
-   date_from
-   date_to
-   q

### GET /issues/{id}

Return complete issue details including attachments, notes and replies.

### PATCH /issues/{id}/status

-   Pending
-   Solved
-   Need Clarification

Write all changes to `issue_status_history`.

## Notes

### GET /issues/{id}/notes

Return notes ordered by creation date.

### POST /issues/{id}/notes

Create administrator notes.

Store in `issue_notes`.

## Replies

### GET /issues/{id}/replies

Return reply history.

### POST /issues/{id}/reply

-   Post reply using the existing Discord bot connection.
-   Persist reply in `issue_replies`.
-   Store Admin User ID, Reply Date, Reply Time and Discord Message ID.

## Dashboard

### GET /dashboard/summary

Return:

-   Total Issues
-   Pending
-   Solved
-   Need Clarification
-   Today's Issues
-   Total Channels

## Validation

Validate every mutation request using Pydantic.

## Logging

Generate structured logs for:

-   Login
-   Logout
-   Status updates
-   Notes
-   Replies
-   Validation failures
-   Discord failures
-   Database failures

## Acceptance Criteria

-   JWT authentication implemented.
-   Admin authorization enforced.
-   All APIs operational.
-   Status history stored.
-   Notes stored.
-   Replies posted to Discord and persisted.
-   Structured logging implemented.
-   Existing functionality remains unaffected.
