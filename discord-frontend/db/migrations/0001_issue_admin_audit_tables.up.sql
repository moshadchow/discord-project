BEGIN;

CREATE TABLE public.issue_status_history (
    id SERIAL PRIMARY KEY,
    issue_id BIGINT NOT NULL REFERENCES public.issues(id),
    previous_status TEXT,
    new_status TEXT NOT NULL,
    changed_by TEXT NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE public.issue_notes (
    id SERIAL PRIMARY KEY,
    issue_id BIGINT NOT NULL REFERENCES public.issues(id),
    note TEXT NOT NULL,
    admin_user_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE public.issue_replies (
    id SERIAL PRIMARY KEY,
    issue_id BIGINT NOT NULL REFERENCES public.issues(id),
    discord_message_id TEXT NOT NULL,
    reply TEXT NOT NULL,
    admin_user_id TEXT NOT NULL,
    reply_date DATE NOT NULL,
    reply_time TIME NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_issue_status_history_issue_id
ON public.issue_status_history(issue_id);

CREATE INDEX idx_issue_notes_issue_id
ON public.issue_notes(issue_id);

CREATE INDEX idx_issue_replies_issue_id
ON public.issue_replies(issue_id);

COMMIT;
