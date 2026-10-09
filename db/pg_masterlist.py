"""CRUD operations on the masterlist table over a direct Postgres connection.

Reads the Opcenter masterlist Excel (data/factory_data) and loads it into the
``public.masterlist`` table using ``DATABASE_URL`` from ``.env``.

Excel layout (first sheet):
    Part No. | Product | Op. No. | Operation Name | Setup Time | Op. Time per Item
Part No. / Product are only filled on the first row of each part (merged cells),
so they are forward-filled. Times look like ``"1 Hours 02.5000 Mins"``.
"""

import os
import re
import sys
from pathlib import Path
from typing import Any, cast, LiteralString

import pandas as pd
from dotenv import load_dotenv

import psycopg
import psycopg.rows


load_dotenv(Path(__file__).resolve().parent.parent / ".env")

Row = dict[str, Any]

_TIME_RE = re.compile(r"(\d+)\s*Hours?\s+(\d+(?:\.\d+)?)\s*Mins?", re.IGNORECASE)

_COLUMNS = ("part_no", "part_name", "operation_no", "operation_name", "setup_sec", "ct_sec")


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def _parse_time_str(text: str) -> float | None:
    m = _TIME_RE.search(text)
    if m:
        return round((float(m.group(1)) * 60.0 + float(m.group(2))) * 60.0, 3)
    try:
        return round(float(text) * 60.0, 3)
    except ValueError:
        return None


def time_to_seconds(raw: object) -> float | None:
    """Convert '1 Hours 02.5000 Mins' or numeric string to seconds. Returns None if unparseable."""
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    text = str(raw).strip()
    if text.lower() in ("unspecified", "nan", "", "none"):
        return None
    return _parse_time_str(text)


def _clean_op_no(raw: object) -> str:
    """Render 10.0 -> '10', keep other values as stripped strings."""
    if isinstance(raw, float) and raw.is_integer():
        return str(int(raw))
    return str(raw).strip()


def parse_masterlist_excel(file_path: str) -> list[Row]:
    """Parse the Opcenter masterlist Excel into rows for the masterlist table."""
    df: pd.DataFrame = pd.read_excel(file_path, sheet_name=0)  # type: ignore[reportUnknownMemberType]
    df.columns = [str(c).strip() for c in df.columns]
    df[["Part No.", "Product"]] = df[["Part No.", "Product"]].ffill()  # type: ignore[reportUnknownMemberType]

    rows: list[Row] = []
    for _, r in df.iterrows():  # type: ignore[reportUnknownVariableType]
        part_no = r["Part No."]
        op_name = r["Operation Name"]
        if pd.isna(part_no) or pd.isna(op_name):  # type: ignore[arg-type]
            continue
        rows.append(
            {
                "part_no": str(part_no).strip(),
                "part_name": str(r["Product"]).strip(),
                "operation_no": _clean_op_no(r["Op. No."]),
                "operation_name": str(op_name).strip(),
                "setup_sec": time_to_seconds(r["Setup Time"]),
                "ct_sec": time_to_seconds(r["Op. Time per Item"]),
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Connection / schema
# ---------------------------------------------------------------------------


def get_connection() -> Any:
    """Open a Postgres connection using DATABASE_URL."""
    if psycopg is None:
        raise RuntimeError("psycopg is not installed or available")
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL is not set in .env")
    return psycopg.connect(url, connect_timeout=15)


def ensure_schema(conn: psycopg.Connection[Any]) -> None:
    """Make sure the masterlist table has every column we write."""
    from psycopg.sql import SQL

    with conn.cursor() as cur:
        cur.execute(
            SQL(
                cast(
                    LiteralString,
                    Path(__file__)
                    .resolve()
                    .parent.parent.joinpath("migrations", "001_masterlist.sql")
                    .read_text(),
                )
            )
        )
        cur.execute(
            SQL(
                cast(
                    LiteralString,
                    Path(__file__)
                    .resolve()
                    .parent.parent.joinpath("migrations", "003_masterlist_excel_columns.sql")
                    .read_text(),
                )
            )
        )
    conn.commit()


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


def create_rows(conn: psycopg.Connection[Any], rows: list[Row], replace: bool = True) -> int:
    """CREATE: insert rows. With replace=True the table is cleared first.

    Runs in a single transaction, so if the insert fails the old data is kept.
    """
    from psycopg.sql import SQL, Identifier, Placeholder

    cols_sql = SQL(", ").join(map(Identifier, _COLUMNS))
    placeholders_sql = SQL(", ").join(Placeholder(c) for c in _COLUMNS)
    query = SQL("INSERT INTO public.masterlist ({}) VALUES ({})").format(cols_sql, placeholders_sql)

    with conn.transaction(), conn.cursor() as cur:
        if replace:
            cur.execute("DELETE FROM public.masterlist")
        cur.executemany(query, rows)
    return len(rows)


def read_rows(
    conn: psycopg.Connection[Any], part_no: str | None = None, limit: int | None = None
) -> list[Row]:
    """READ: fetch rows, optionally filtered by part_no."""
    from psycopg.sql import SQL, Identifier

    cols_sql = SQL(", ").join(map(Identifier, _COLUMNS))
    query = SQL("SELECT id, {} FROM public.masterlist").format(cols_sql)

    params: list[Any] = []
    if part_no is not None:
        query += SQL(" WHERE part_no = %s")
        params.append(part_no)
    query += SQL(" ORDER BY id")
    if limit is not None:
        query += SQL(" LIMIT %s")
        params.append(limit)
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:  # type: ignore[reportUnknownMemberType,reportUnknownArgumentType]
        cur.execute(query, params)
        return list(cur.fetchall())  # type: ignore[reportUnknownArgumentType]


def count_rows(conn: psycopg.Connection[Any]) -> int:
    """READ: total number of rows."""
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM public.masterlist")
        res = cur.fetchone()
        return int(res[0]) if res else 0


def update_row(conn: psycopg.Connection[Any], row_id: int, **fields: Any) -> int:
    """UPDATE: change the given columns on one row. Returns rows affected."""
    bad = set(fields) - set(_COLUMNS)
    if bad:
        raise ValueError(f"Unknown columns: {sorted(bad)}")
    if not fields:
        return 0
    from psycopg.sql import SQL, Identifier, Placeholder

    assignments = SQL(", ").join(
        SQL("{} = {}").format(Identifier(c), Placeholder(c)) for c in fields
    )
    query = SQL("UPDATE public.masterlist SET {} WHERE id = %(id)s").format(assignments)
    with conn.transaction(), conn.cursor() as cur:
        cur.execute(query, {**fields, "id": row_id})
        return cur.rowcount


def delete_row(conn: psycopg.Connection[Any], row_id: int) -> int:
    """DELETE: remove one row by id. Returns rows affected."""
    with conn.transaction(), conn.cursor() as cur:
        cur.execute("DELETE FROM public.masterlist WHERE id = %s", (row_id,))
        return cur.rowcount


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _demo_crud(conn: psycopg.Connection[Any]) -> None:
    """Run C/R/U/D on a throwaway demo row, leaving real data untouched."""
    demo: Row = {
        "part_no": "__DEMO__",
        "part_name": "Demo part",
        "operation_no": "10",
        "operation_name": "Turning 1st",
        "setup_sec": 600.0,
        "ct_sec": 30.0,
    }
    create_rows(conn, [demo], replace=False)
    row = read_rows(conn, part_no="__DEMO__")[0]
    print(f"  CREATE + READ -> {row}")
    update_row(conn, row["id"], ct_sec=45.0)
    print(f"  UPDATE        -> {read_rows(conn, part_no='__DEMO__')[0]}")
    delete_row(conn, row["id"])
    print(f"  DELETE        -> remaining demo rows: {len(read_rows(conn, part_no='__DEMO__'))}")


def main(argv: list[str]) -> None:
    if len(argv) < 2:
        print("Usage: python -m db.pg_masterlist <masterlist.xls> [--demo-crud]")
        return
    rows = parse_masterlist_excel(argv[1])
    print(f"Parsed {len(rows)} rows from {argv[1]}")
    with get_connection() as conn:
        ensure_schema(conn)
        inserted = create_rows(conn, rows, replace=True)
        print(f"Uploaded {inserted} rows. Table now has {count_rows(conn)} rows.")
        if "--demo-crud" in argv:
            print("Running CRUD demo on a temporary row:")
            _demo_crud(conn)
            print(f"Final row count: {count_rows(conn)}")


if __name__ == "__main__":
    main(sys.argv)
