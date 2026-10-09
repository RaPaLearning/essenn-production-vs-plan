-- Sheet "Templet": example routings with resource per operation.
-- Stored as-is (no forward-fill) because it mixes parts, child parts and purchase items.
CREATE TABLE IF NOT EXISTS public.masterlist_template (
    id             SERIAL PRIMARY KEY,
    excel_row      INTEGER,
    sl_no          INTEGER,
    part_no        TEXT,
    product        TEXT,
    operation_no   TEXT,
    operation_name TEXT,
    setup_time_raw TEXT,
    op_time_raw    TEXT,
    setup_sec      NUMERIC,
    ct_sec         NUMERIC,
    resource       TEXT
);

ALTER TABLE public.masterlist_template ENABLE ROW LEVEL SECURITY;
