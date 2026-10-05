-- Sheet "Machine list": machine -> group / sub group
CREATE TABLE IF NOT EXISTS public.machines (
    id         SERIAL PRIMARY KEY,
    excel_row  INTEGER,
    sl_no      INTEGER,
    machine    TEXT NOT NULL,
    main_group TEXT,
    sub_group  TEXT
);

ALTER TABLE public.machines ENABLE ROW LEVEL SECURITY;
