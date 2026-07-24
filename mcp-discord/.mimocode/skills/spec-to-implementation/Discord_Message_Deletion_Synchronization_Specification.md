# Synchronize Discord Message Deletion with the `issues` Table

## Objective

Enhance the existing Discord MCP server so that when a Discord message
is deleted from a monitored channel, the corresponding issue record is
automatically removed from the `issues` table in the **mcp_discord**
PostgreSQL database.

The implementation must reuse the existing Discord event system and
repository architecture without duplicating business logic.

## Business Requirement

When a Discord message that was previously captured as an issue is
deleted, the corresponding database record must also be deleted to keep
the database synchronized with Discord.

## Functional Requirements

### Discord Event

-   Listen for the `on_message_delete` event.
-   Process only monitored channels.
-   Ignore unrelated channels.

### Deletion Flow

1.  Receive the message deletion event.
2.  Read the Discord Message ID.
3.  Find the matching record using `discord_message_id`.
4.  Delete the corresponding row from the `issues` table.
5.  Log the result.

If no matching record exists, log the event and continue.

## Repository

Extend `IssuesRepository` with a delete method using
`discord_message_id`.

## Error Handling

-   Log database errors.
-   Continue processing subsequent events.
-   Do not terminate the Discord bot.

## Logging

Log:

-   Message deletion detected
-   Discord Message ID
-   Issue deleted
-   No matching issue found
-   Database deletion failures

## Testing

Test:

-   Successful deletion
-   Missing issue
-   Database failure
-   Monitored vs. unmonitored channels

## Acceptance Criteria

-   Deleting a Discord message deletes the matching issue record.
-   Matching uses `discord_message_id`.
-   Missing records are handled gracefully.
-   Existing issue capture remains unchanged.
