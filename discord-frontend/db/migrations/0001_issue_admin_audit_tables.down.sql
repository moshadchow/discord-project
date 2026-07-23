BEGIN;

DROP INDEX IF EXISTS public.idx_issue_replies_issue_id;
DROP INDEX IF EXISTS public.idx_issue_notes_issue_id;
DROP INDEX IF EXISTS public.idx_issue_status_history_issue_id;

DROP TABLE IF EXISTS public.issue_replies;
DROP TABLE IF EXISTS public.issue_notes;
DROP TABLE IF EXISTS public.issue_status_history;

COMMIT;
