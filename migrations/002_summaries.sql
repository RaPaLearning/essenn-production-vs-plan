CREATE TABLE public.summaries (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    shift TEXT NOT NULL,
    machine TEXT,
    job_order_no TEXT,
    total_qty NUMERIC,
    part_no TEXT,
    part_name TEXT,
    operation TEXT,
    plan_qty NUMERIC,
    ok_qty NUMERIC,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);
