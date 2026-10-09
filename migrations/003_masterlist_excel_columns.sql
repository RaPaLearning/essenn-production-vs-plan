-- Sheet "As on 16-05-2026": keep the original Excel text next to the parsed numbers
ALTER TABLE public.masterlist
    ADD COLUMN IF NOT EXISTS excel_row      INTEGER,
    ADD COLUMN IF NOT EXISTS setup_time_raw TEXT,
    ADD COLUMN IF NOT EXISTS op_time_raw    TEXT,
    ADD COLUMN IF NOT EXISTS setup_sec      NUMERIC;
