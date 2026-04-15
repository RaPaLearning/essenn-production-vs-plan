import datetime
import sys
import os
from typing import Any
import unittest

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


class TestGetActiveJobs(unittest.TestCase):

    # --- _parse_start_date ---

    def test_parse_start_date_valid(self) -> None:
        row = _make_row("X", "10/03/2026", "15/03/2026")
        self.assertEqual(_parse_start_date(row), datetime.date(2026, 3, 10))  # pyright: ignore[reportPrivateUsage]

    def test_parse_start_date_nan(self) -> None:
        row = _make_row("X", None, "15/03/2026")
        self.assertIsNone(_parse_start_date(row))  # pyright: ignore[reportPrivateUsage]

    def test_parse_start_date_unparseable(self) -> None:
        row = _make_row("X", "not-a-date", "15/03/2026")
        self.assertIsNone(_parse_start_date(row))  # pyright: ignore[reportPrivateUsage]

    # --- _parse_end_date ---

    def test_parse_end_date_valid(self) -> None:
        row = _make_row("X", "10/03/2026", "15/03/2026")
        self.assertEqual(_parse_end_date(row), datetime.date(2026, 3, 15))  # pyright: ignore[reportPrivateUsage]

    def test_parse_end_date_nan(self) -> None:
        row = _make_row("X", "10/03/2026", None)
        self.assertIsNone(_parse_end_date(row))  # pyright: ignore[reportPrivateUsage]

    def test_parse_end_date_unparseable(self) -> None:
        row = _make_row("X", "10/03/2026", "not-a-date")
        self.assertIsNone(_parse_end_date(row))  # pyright: ignore[reportPrivateUsage]

    # --- _process_row ---

    def test_process_row_order_nan(self) -> None:
        row = _make_row(None, "10/03/2026", "15/03/2026")
        self.assertIsNone(_process_row(row, datetime.date(2026, 3, 12)))  # pyright: ignore[reportPrivateUsage]

    def test_process_row_start_none(self) -> None:
        row = _make_row("J001", "not-a-date", "15/03/2026")
        self.assertIsNone(_process_row(row, datetime.date(2026, 3, 12)))  # pyright: ignore[reportPrivateUsage]

    def test_process_row_end_none(self) -> None:
        row = _make_row("J001", "10/03/2026", "not-a-date")
        self.assertIsNone(_process_row(row, datetime.date(2026, 3, 12)))  # pyright: ignore[reportPrivateUsage]

    # --- _process_sheet ---

    def test_process_sheet_too_few_rows(self) -> None:
        df = pd.DataFrame([[1, 2, 3]])  # only 1 row, < 6
        self.assertEqual(_process_sheet(df, datetime.date(2026, 3, 10)), [])  # pyright: ignore[reportPrivateUsage]

    # --- get_active_jobs (integration) ---

    def test_jobs_spanning_date(self) -> None:
        jobs = get_active_jobs(FIXTURE, "2026-03-10")

        self.assertIn("J2602-0028", jobs)
        self.assertIn("J2601-0054", jobs)
        self.assertIn("J2603-0072/97", jobs)

    def test_job_not_spanning_date(self) -> None:
        jobs = get_active_jobs(FIXTURE, "2026-03-20")

        self.assertNotIn("J2602-0020", jobs)

    def test_empty_date_returns_nothing(self) -> None:
        jobs = get_active_jobs(FIXTURE, "2026-01-01")

        self.assertEqual(jobs, [])


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
