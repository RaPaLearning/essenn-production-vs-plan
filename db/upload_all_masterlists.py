"""Upload all sheets from the Excel masterlist to PostgreSQL.

Sheets handled:
1. 'As on 16-05-2026' -> public.masterlist
2. 'Machine list'     -> public.machines
3. 'Templet'          -> public.masterlist_template
"""

import os
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

import psycopg
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

from db.pg_masterlist import time_to_seconds


def clean_str(val: object) -> str | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    return s if s else None


def clean_int(val: object) -> int | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def clean_op_no(raw: object) -> str | None:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    if isinstance(raw, float) and raw.is_integer():
        return str(int(raw))
    s = str(raw).strip()
    return s if s else None


def get_connection() -> Any:
    if psycopg is None:
        raise RuntimeError("psycopg is not installed or available")
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL is not set in .env")
    return psycopg.connect(url, connect_timeout=15)


def apply_migrations(conn: psycopg.Connection[Any]) -> None:
    """Execute all SQL migration files in order."""
    migrations_dir = PROJECT_ROOT / "migrations"
    sql_files = sorted(migrations_dir.glob("*.sql"))
    with conn.cursor() as cur:
        for sql_file in sql_files:
            print(f"Applying migration: {sql_file.name}")
            sql = sql_file.read_text(encoding="utf-8")
            cur.execute(sql)
    conn.commit()


# ---------------------------------------------------------------------------
# Sheet 1: As on 16-05-2026 -> public.masterlist
# ---------------------------------------------------------------------------
def upload_main_sheet(conn: psycopg.Connection[Any], xl: pd.ExcelFile) -> int:
    sheet_name = "As on 16-05-2026"
    df = xl.parse(sheet_name)
    df.columns = [str(c).strip() for c in df.columns]

    # Forward-fill Part No. and Product
    df[["Part No.", "Product"]] = df[["Part No.", "Product"]].ffill()

    rows: list[dict[str, Any]] = []
    for idx, r in df.iterrows():
        part_no = clean_str(r.get("Part No."))
        op_name = clean_str(r.get("Operation Name"))
        if not part_no and not op_name:
            continue

        setup_raw = clean_str(r.get("Setup Time"))
        op_raw = clean_str(r.get("Op. Time per Item"))

        rows.append(
            {
                "excel_row": int(idx) + 2,  # 1-indexed Excel row (header is row 1)
                "part_no": part_no or "",
                "part_name": clean_str(r.get("Product")),
                "operation_no": clean_op_no(r.get("Op. No.")),
                "operation_name": op_name,
                "setup_time_raw": setup_raw,
                "op_time_raw": op_raw,
                "setup_sec": time_to_seconds(setup_raw),
                "ct_sec": time_to_seconds(op_raw),
            }
        )

    with conn.transaction(), conn.cursor() as cur:
        cur.execute("DELETE FROM public.masterlist")
        cols = [
            "excel_row",
            "part_no",
            "part_name",
            "operation_no",
            "operation_name",
            "setup_time_raw",
            "op_time_raw",
            "setup_sec",
            "ct_sec",
        ]
        from psycopg.sql import SQL, Identifier, Placeholder
        cols_sql = SQL(", ").join(map(Identifier, cols))
        placeholders_sql = SQL(", ").join(Placeholder(c) for c in cols)
        query = SQL("INSERT INTO public.masterlist ({}) VALUES ({})").format(cols_sql, placeholders_sql)
        cur.executemany(query, rows)

    print(f"Uploaded {len(rows)} rows into public.masterlist")
    return len(rows)


# ---------------------------------------------------------------------------
# Sheet 2: Machine list -> public.machines
# ---------------------------------------------------------------------------
def upload_machine_list(conn: psycopg.Connection[Any], xl: pd.ExcelFile) -> int:
    df = xl.parse("Machine list", header=None)
    # Data starts at index 6 (row 7 in Excel)
    df_data = df.iloc[6:].reset_index(drop=True)

    rows: list[dict[str, Any]] = []
    for idx, r in df_data.iterrows():
        sl_no = clean_int(r.iloc[1])
        machine = clean_str(r.iloc[2])
        if not machine:
            continue

        rows.append(
            {
                "excel_row": int(idx) + 7,
                "sl_no": sl_no,
                "machine": machine,
                "main_group": clean_str(r.iloc[3]),
                "sub_group": clean_str(r.iloc[4]),
            }
        )

    with conn.transaction(), conn.cursor() as cur:
        cur.execute("DELETE FROM public.machines")
        cols = ["excel_row", "sl_no", "machine", "main_group", "sub_group"]
        from psycopg.sql import SQL, Identifier, Placeholder
        cols_sql = SQL(", ").join(map(Identifier, cols))
        placeholders_sql = SQL(", ").join(Placeholder(c) for c in cols)
        query = SQL("INSERT INTO public.machines ({}) VALUES ({})").format(cols_sql, placeholders_sql)
        cur.executemany(query, rows)

    print(f"Uploaded {len(rows)} rows into public.machines")
    return len(rows)


# ---------------------------------------------------------------------------
# Sheet 3: Templet -> public.masterlist_template
# ---------------------------------------------------------------------------
def upload_template_sheet(conn: psycopg.Connection[Any], xl: pd.ExcelFile) -> int:
    df = xl.parse("Templet")
    df.columns = [str(c).strip() for c in df.columns]

    rows: list[dict[str, Any]] = []
    for idx, r in df.iterrows():
        setup_raw = clean_str(r.get("Setup Time"))
        op_raw = clean_str(r.get("Op. Time per Item"))

        rows.append(
            {
                "excel_row": int(idx) + 2,
                "sl_no": clean_int(r.get("SL No")),
                "part_no": clean_str(r.get("Part No.")),
                "product": clean_str(r.get("Product")),
                "operation_no": clean_op_no(r.get("Op. No.")),
                "operation_name": clean_str(r.get("Operation Name")),
                "setup_time_raw": setup_raw,
                "op_time_raw": op_raw,
                "setup_sec": time_to_seconds(setup_raw),
                "ct_sec": time_to_seconds(op_raw),
                "resource": clean_str(r.get("Resource")),
            }
        )

    with conn.transaction(), conn.cursor() as cur:
        cur.execute("DELETE FROM public.masterlist_template")
        cols = [
            "excel_row",
            "sl_no",
            "part_no",
            "product",
            "operation_no",
            "operation_name",
            "setup_time_raw",
            "op_time_raw",
            "setup_sec",
            "ct_sec",
            "resource",
        ]
        from psycopg.sql import SQL, Identifier, Placeholder
        cols_sql = SQL(", ").join(map(Identifier, cols))
        placeholders_sql = SQL(", ").join(Placeholder(c) for c in cols)
        query = SQL("INSERT INTO public.masterlist_template ({}) VALUES ({})").format(cols_sql, placeholders_sql)
        cur.executemany(query, rows)

    print(f"Uploaded {len(rows)} rows into public.masterlist_template")
    return len(rows)


def main(file_path: str) -> None:
    print(f"Opening Excel file: {file_path}")
    xl = pd.ExcelFile(file_path)
    print(f"Found sheets: {xl.sheet_names}")

    with get_connection() as conn:
        print("Connected to PostgreSQL database.")
        apply_migrations(conn)

        if "As on 16-05-2026" in xl.sheet_names:
            upload_main_sheet(conn, xl)
        if "Machine list" in xl.sheet_names:
            upload_machine_list(conn, xl)
        if "Templet" in xl.sheet_names:
            upload_template_sheet(conn, xl)

    print("Database upload complete!")


if __name__ == "__main__":
    excel_file = (
        sys.argv[1]
        if len(sys.argv) > 1
        else str(
            PROJECT_ROOT
            / "data"
            / "factory_data"
            / "Mater list of Component(Preactor)-1 (1) (1).xls"
        )
    )
    main(excel_file)
