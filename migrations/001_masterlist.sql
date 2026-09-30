CREATE TABLE public.masterlist (
    id SERIAL PRIMARY KEY,
    part_no TEXT NOT NULL,
    part_name TEXT,
    operation_no TEXT,
    operation_name TEXT,
    resource TEXT,
    ct_sec NUMERIC,
    machine_type TEXT
);
