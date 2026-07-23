# Phase 1 --- Database Schema Specification

## Objective

Extend the PostgreSQL schema to support issue status history,
administrator notes, and Discord reply history while reusing the
existing `public.issues` table. The changes must be additive only and
implemented through database migrations.

------------------------------------------------------------------------

## Scope

-   Reuse the existing `public.issues` table.
-   Create three new tables.
-   Add indexes for efficient lookups.
-   Implement changes using migration scripts only.
-   Do not perform destructive changes to existing tables or data.

------------------------------------------------------------------------

## Database Changes

### 1. `issue_status_history`

Tracks every status transition for an issue.

``` sql
CREATE TABLE issue_status_history (
    id SERIAL PRIMARY KEY,
    issue_id BIGINT NOT NULL REFERENCES issues(id),
    previous_status TEXT,
    new_status TEXT NOT NULL,
    changed_by TEXT NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

------------------------------------------------------------------------

### 2. `issue_notes`

Stores internal administrator notes.

``` sql
CREATE TABLE issue_notes (
    id SERIAL PRIMARY KEY,
    issue_id BIGINT NOT NULL REFERENCES issues(id),
    note TEXT NOT NULL,
    admin_user_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

------------------------------------------------------------------------

### 3. `issue_replies`

Stores replies sent back to Discord.

``` sql
CREATE TABLE issue_replies (
    id SERIAL PRIMARY KEY,
    issue_id BIGINT NOT NULL REFERENCES issues(id),
    discord_message_id TEXT NOT NULL,
    reply TEXT NOT NULL,
    admin_user_id TEXT NOT NULL,
    reply_date DATE NOT NULL,
    reply_time TIME NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

------------------------------------------------------------------------

## Indexes

Create indexes on `issue_id` for all new tables.

``` sql
CREATE INDEX idx_issue_status_history_issue_id
ON issue_status_history(issue_id);

CREATE INDEX idx_issue_notes_issue_id
ON issue_notes(issue_id);

CREATE INDEX idx_issue_replies_issue_id
ON issue_replies(issue_id);
```

------------------------------------------------------------------------

## Migration Requirements

-   Use versioned migration scripts.
-   Existing `issues` data must remain intact.
-   No destructive schema changes.
-   Migrations must be reversible where supported.

------------------------------------------------------------------------

## Acceptance Criteria

-   Three new tables are created successfully.
-   Foreign key relationships reference `issues(id)`.
-   Indexes exist on `issue_id` in all new tables.
-   Existing `issues` table remains unchanged.
-   Migrations execute successfully on a clean and existing database.
