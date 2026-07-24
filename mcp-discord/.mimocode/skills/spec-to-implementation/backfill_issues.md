# Add `seed.py` to Import Historical Discord Issues

## Objective

Create a standalone `seed.py` script to backfill historical issue data from a Discord channel into the PostgreSQL `issues` table.

The script should retrieve historical messages from a specified Discord channel, extract issue information from each message, and populate the `issues` table using the same extraction and persistence logic as the real-time message listener.

This script is intended for one-time or periodic historical data seeding and must not interfere with the MCP server's normal operation.

---

# Input

The script should accept the **Discord channel name** as a command-line parameter.

## Example

```bash
python seed.py --channel "support-issues"
```

### Optional Parameters

```bash
python seed.py --channel "support-issues" --limit 500

python seed.py --channel "support-issues" \
  --from-date 2026-01-01 \
  --to-date 2026-06-30
```

---

# Message Retrieval

- Locate the Discord channel by its name.
- Retrieve historical messages using the Discord API.
- Handle pagination automatically to retrieve all available messages (or the specified limit).
- Process messages in chronological order (oldest to newest) to preserve history.

---

# Issue Extraction

For each historical message, extract the following information:

| Field | Description |
|--------|-------------|
| `issue_date` | Date extracted from the message. If no explicit date exists, use the Discord message timestamp. |
| `issue_time` | Time extracted from the message. If no explicit time exists, use the Discord message timestamp. |
| `sender` | Discord username or display name of the message author. |
| `issue` | The issue description extracted from the message body. |

### Additional Metadata

Populate the following fields as well:

- Discord Message ID
- Guild ID
- Guild Name
- Channel ID
- Channel Name
- Message Timestamp (UTC)
- Created At
- Updated At

> **Note:** Reuse the same parsing logic implemented for the real-time listener to ensure consistent data extraction.

---

# Database Persistence

Insert the extracted records into the PostgreSQL `issues` table.

### Requirements

- Use the existing PostgreSQL connection and ORM/database layer.
- Use transactions where appropriate.
- Use parameterized queries or ORM methods.
- Reuse the existing repository/service responsible for saving issues.

---

# Duplicate Prevention

Prevent duplicate inserts using the Discord Message ID.

If a record already exists:

- Skip the insert.
- Log that the message has already been imported.
- Continue processing the remaining messages.

---

# Logging

Log the following information during execution:

- Channel being processed
- Total messages retrieved
- Total issues extracted
- Records inserted
- Duplicate records skipped
- Failed records
- Processing duration
- Final summary

---

# Error Handling

- Continue processing if an individual message cannot be parsed.
- Continue processing if a database insert fails for a single record.
- Log all failures with sufficient detail for troubleshooting.
- Do not terminate the import because of a single failed message.

---

# Code Organization

Create a dedicated script:

```text
seed.py
```

The script should:

- Reuse the existing Discord client configuration.
- Reuse the existing issue extraction logic.
- Reuse the existing repository/service responsible for persisting issues.
- Avoid duplicating business logic already implemented in the real-time listener.
- Follow the existing project architecture and coding conventions.

---

# Configuration

Use the existing environment/configuration mechanism for:

- Discord Bot Token
- PostgreSQL connection
- Logging configuration

Do **not** hardcode:

- Discord Bot Token
- Database credentials
- Guild IDs
- Channel IDs

---

# Acceptance Criteria

- `seed.py` imports historical messages from a specified Discord channel.
- The channel name is supplied as a command-line parameter.
- Historical messages are processed from oldest to newest.
- Issues are extracted using the same logic as the real-time listener.
- Duplicate records are skipped using the Discord Message ID.
- Existing data remains intact.
- Detailed progress and summary logs are generated.
- The script can be executed independently without affecting the MCP server.
- The implementation follows the existing project architecture and is maintainable for future enhancements.