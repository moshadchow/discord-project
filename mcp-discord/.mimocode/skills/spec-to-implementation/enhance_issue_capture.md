# Enhance Discord Issue Capture to Store Message Attachments in the `issues` Table

## Objective

Based on the existing project architecture described in `AGENTS.md`,
enhance the Discord issue capture process to store message attachments
along with the issue details in the `issues` table of the
**discord-mcp** PostgreSQL database. The implementation should reuse the
existing event handling, issue capture, parser, and repository
architecture without duplicating business logic.

## Business Requirement

Currently, when an issue is captured from a monitored Discord channel,
only the message content and extracted issue details are stored in the
database.

Enhance the solution so that **all attachments associated with the
Discord message** are also captured and persisted in the `issues` table.

### Supported Attachments

-   Images (PNG, JPG, JPEG, GIF, WEBP)
-   PDF documents
-   Text files
-   Log files
-   ZIP archives
-   Any other file type supported by Discord

## Database Changes

Update the `issues` table to support multiple attachments per Discord
message.

Store:

-   Attachment Name
-   Original File Name
-   Discord Attachment URL (CDN URL)
-   Content Type (MIME Type)
-   File Size (Bytes)

Design the solution to support multiple attachments without requiring
future schema redesign (e.g., JSON/JSONB or a normalized child table).

## Issue Capture Flow

1.  Capture the issue using the existing `IssueCaptureService`.
2.  Extract issue details using the existing parser.
3.  Read all message attachments.
4.  Persist the attachment metadata with the issue record.
5.  Continue using the existing duplicate detection based on the Discord
    Message ID.

Do not create duplicate attachment records if the same Discord message
has already been processed.

## Message Processing

For each attachment capture:

-   File Name
-   File Extension
-   Content Type
-   File Size
-   Discord CDN URL

If no attachments exist, continue processing normally and store an empty
attachment collection or `NULL`, depending on the schema.

## Repository Changes

Update `IssuesRepository` to:

-   Save attachment metadata.
-   Retrieve attachment information when reading issues.
-   Reuse the existing insert/update workflow.
-   Avoid duplicating repository logic.

## Error Handling

-   Log attachment metadata errors and continue storing the issue.
-   Continue processing remaining attachments if one fails.
-   Attachment failures must not prevent issue capture.

## Logging

Log:

-   Number of attachments detected
-   Attachment names
-   Successful persistence
-   Processing failures
-   Duplicate issue detection

Do not log attachment contents or sensitive information.

## Testing

Add or update tests for:

-   No attachments
-   Single attachment
-   Multiple attachments
-   Different attachment types
-   Duplicate message handling
-   Database persistence
-   Error handling

## Code Organization

-   Keep Discord event handling in `server.py`.
-   Reuse `IssueCaptureService`.
-   Extend `IssueRecord` as needed.
-   Update `IssuesRepository`.
-   Reuse duplicate detection.
-   Avoid duplicating parsing or persistence logic.

## Acceptance Criteria

-   Attachment metadata is stored with each issue.
-   Multiple attachments are supported.
-   Existing issue capture remains unchanged.
-   Duplicate detection continues to work.
-   Attachment failures do not interrupt issue capture.
-   The implementation follows the architecture defined in `AGENTS.md`.
