# Build a React + TypeScript Admin Portal for Managing Discord Issues

## Objective

Build a modern **React + TypeScript** web application that enables authorized administrators to manage issues automatically captured from Discord. The application will allow administrators to review issues from multiple Discord channels, update their status, communicate with users directly from the application, and maintain a complete audit trail.

The solution must integrate with the existing **mcp-discord** backend and PostgreSQL database while following the project architecture defined in `AGENTS.md`.

---

# Technology Stack

## Frontend

* React 18+
* TypeScript
* Vite
* React Router
* TanStack Query (React Query)
* Axios
* Tailwind CSS
* React Hook Form
* Zod
* Day.js
* Heroicons (or similar)

## Backend

Reuse the existing Python MCP server.

Expose REST APIs (or extend the current backend) for:

* Authentication
* Issue management
* Reply management
* Status updates
* Channel listing
* Sending Discord replies

Do not duplicate existing Discord integration logic.

---

# Authentication

Only authenticated administrators can access the application.

Required features:

* Login
* Logout
* JWT authentication
* Session timeout
* Refresh token support (if already implemented)
* Route protection

---

# Application Layout

The application should follow a three-panel layout.

```
---------------------------------------------------------------
 Header
---------------------------------------------------------------
| Channels | Conversation & Attachments | Issue Details        |
|          |                            |                      |
|          |                            | Status               |
|          |                            | Notes               |
|          |                            | Reply               |
---------------------------------------------------------------
```

---

# Left Panel - Channel List

Display all monitored Discord channels.

Each channel should show:

* Channel Name
* Number of unresolved issues
* Last activity time

Features:

* Search channels
* Sort by latest activity
* Badge showing Pending issue count
* Auto-refresh when new issues arrive

Selecting a channel loads its conversation.

---

# Center Panel - Conversation

Display all captured messages for the selected channel.

Each issue card should contain:

* Sender
* Message Date
* Message Time
* Original Issue
* Attachments
* Current Status
* Reply History
* Last Updated

Display messages chronologically.

Support infinite scrolling or pagination.

---

# Attachment Viewer

Display attachments directly inside the conversation.

Support:

* Images
* PDF
* Text files
* ZIP (download only)
* Other files (download link)

Image attachments should open in a preview modal.

Non-image attachments should display:

* File name
* File size
* Download button

Use the existing `attachments` JSONB column.

---

# Right Panel - Issue Details

When an issue is selected, display detailed information.

Fields:

* Discord Message ID
* Guild
* Channel
* Sender
* Issue Date
* Issue Time
* Created Date
* Current Status
* Notes
* Reply History

---

# Issue Status

Administrators can update the issue status.

Supported values:

* Pending
* Solved
* Need Clarification

The status dropdown should be editable.

Every status update must be persisted immediately.

---

# Notes

Administrators can maintain internal notes.

Requirements:

* Rich text not required
* Plain text
* Unlimited updates
* Notes are internal only
* Notes are not sent to Discord

Store:

* Note
* Admin User ID
* Created Date
* Updated Date

Display notes chronologically.

---

# Reply to Discord

Administrators can send replies directly to the original Discord channel.

Features:

* Reply textbox
* Send button
* Reply preview
* Attachment support (optional for future enhancement)

When the reply is sent:

* Post the message to the originating Discord channel.
* Associate the reply with the original issue.
* Update the conversation immediately.

Reuse the existing Discord bot connection.

Do not create a separate Discord client.

---

# Reply Audit Trail

Every reply must be stored.

Capture:

* Issue ID
* Discord Message ID
* Reply Text
* Admin User ID
* Reply Date
* Reply Time
* Created Timestamp

The audit history must never be overwritten.

---

# Database Changes

Create new tables as required.

## issue_status_history

Track every status change.

Suggested fields:

* id
* issue_id
* previous_status
* new_status
* changed_by
* changed_at

---

## issue_notes

Store administrator notes.

Suggested fields:

* id
* issue_id
* note
* admin_user_id
* created_at
* updated_at

---

## issue_replies

Store replies sent to Discord.

Suggested fields:

* id
* issue_id
* discord_message_id
* reply
* admin_user_id
* reply_date
* reply_time
* created_at

---

# Existing Issues Table

Continue using the existing `public.issues` table as the primary source of captured Discord issues.

Do not duplicate issue data.

Reuse the existing `attachments` JSONB column for rendering attachments.

---

# Search

Provide global search.

Search by:

* Issue text
* Sender
* Channel
* Status
* Date Range

---

# Filters

Support filtering by:

* Channel
* Status
* Date
* Sender

Filters should work together.

---

# Dashboard

Display summary cards.

Examples:

* Total Issues
* Pending
* Solved
* Need Clarification
* Today's Issues
* Total Channels

---

# Notifications

Notify administrators when:

* A new issue arrives.
* A reply fails.
* Status update fails.
* Reply is successfully sent.

---

# Security

* JWT authentication
* Role-based authorization
* Only Admin users can update issues.
* Validate all inputs.
* Protect against XSS and CSRF where applicable.

---

# Logging

Log:

* Login
* Logout
* Status changes
* Notes added
* Replies sent
* Discord API failures
* Database failures

---

# Testing

Add tests covering:

* Login
* Channel loading
* Issue listing
* Attachment rendering
* Status updates
* Notes
* Reply submission
* Reply history
* Search and filters
* API error handling

---

# Acceptance Criteria

* Administrators can securely log in.
* Channels are displayed in the left navigation panel.
* Selecting a channel loads its conversations and attachments.
* Attachments are displayed correctly from the `attachments` JSONB column.
* Administrators can change the issue status to **Pending**, **Solved**, or **Need Clarification**.
* Administrators can add internal notes to an issue.
* Administrators can reply directly to the originating Discord channel.
* Every reply stores the **Admin User ID**, **Reply Date**, and **Reply Time** in the database.
* Complete status, note, and reply history is preserved.
* The application integrates with the existing **mcp-discord** backend and follows the architecture defined in `AGENTS.md`.
* Existing issue capture and Discord integration continue to function without regression.
