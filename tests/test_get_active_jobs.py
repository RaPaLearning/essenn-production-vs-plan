import datetime
import sys
import os
from typing import Any

import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from get_active_jobs import (
    _parse_start_date,  # pyright: ignore[reportPrivateUsage]
    _parse_end_date,  # pyright: ignore[reportPrivateUsage]
    _process_row,  # pyright: ignore[reportPrivateUsage]
    _process_sheet,  # pyright: ignore[reportPrivateUsage]
    get_active_jobs,
)

FIXTURE = "tests/fixtures/test_operations.xlsx"


def _make_row(order: object, start: object, end: object) -> "pd.Series[Any]":
    """Build a minimal Series matching the column layout the code expects."""
    data: list[object] = [order] + [None] * 7 + [start] + [None] + [end]
    return pd.Series(data)  # type: ignore[reportReturnType]


# --- _parse_start_date ---


def test_parse_start_date_valid() -> None:
    row = _make_row("X", "10/03/2026", "15/03/2026")
    assert _parse_start_date(row) == datetime.date(2026, 3, 10)  # pyright: ignore[reportPrivateUsage]  # nosec B101


def test_parse_start_date_nan() -> None:
    row = _make_row("X", None, "15/03/2026")
    assert _parse_start_date(row) is None  # pyright: ignore[reportPrivateUsage]  # nosec B101


def test_parse_start_date_unparseable() -> None:
    row = _make_row("X", "not-a-date", "15/03/2026")
    assert _parse_start_date(row) is None  # pyright: ignore[reportPrivateUsage]  # nosec B101


# --- _parse_end_date ---


def test_parse_end_date_valid() -> None:
    row = _make_row("X", "10/03/2026", "15/03/2026")
    assert _parse_end_date(row) == datetime.date(2026, 3, 15)  # pyright: ignore[reportPrivateUsage]  # nosec B101


def test_parse_end_date_nan() -> None:
    row = _make_row("X", "10/03/2026", None)
    assert _parse_end_date(row) is None  # pyright: ignore[reportPrivateUsage]  # nosec B101


def test_parse_end_date_unparseable() -> None:
    row = _make_row("X", "10/03/2026", "not-a-date")
    assert _parse_end_date(row) is None  # pyright: ignore[reportPrivateUsage]  # nosec B101


# --- _process_row ---


def test_process_row_order_nan() -> None:
    row = _make_row(None, "10/03/2026", "15/03/2026")
    assert _process_row(row, datetime.date(2026, 3, 12)) is None  # pyright: ignore[reportPrivateUsage]  # nosec B101


def test_process_row_start_none() -> None:
    row = _make_row("J001", "not-a-date", "15/03/2026")
    assert _process_row(row, datetime.date(2026, 3, 12)) is None  # pyright: ignore[reportPrivateUsage]  # nosec B101


def test_process_row_end_none() -> None:
    row = _make_row("J001", "10/03/2026", "not-a-date")
    assert _process_row(row, datetime.date(2026, 3, 12)) is None  # pyright: ignore[reportPrivateUsage]  # nosec B101


# --- _process_sheet ---


def test_process_sheet_too_few_rows() -> None:
    df = pd.DataFrame([[1, 2, 3]])  # only 1 row, < 6
    assert _process_sheet(df, datetime.date(2026, 3, 10)) == []  # pyright: ignore[reportPrivateUsage]  # nosec B101


# --- get_active_jobs (integration) ---


def test_jobs_spanning_date() -> None:
    jobs = get_active_jobs(FIXTURE, "2026-03-10")

    assert "J2602-0028" in jobs  # nosec B101
    assert "J2601-0054" in jobs  # nosec B101
    assert "J2603-0072/97" in jobs  # nosec B101


def test_job_not_spanning_date() -> None:
    jobs = get_active_jobs(FIXTURE, "2026-03-20")

    assert "J2602-0020" not in jobs  # nosec B101


def test_empty_date_returns_nothing() -> None:
    jobs = get_active_jobs(FIXTURE, "2026-01-01")

    assert jobs == []  # nosec B101
