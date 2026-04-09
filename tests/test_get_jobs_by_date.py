"""Tests for get_jobs_by_date — based on the real sample data file.

Fixture: data/sample/OperationsByDay.xlsx
(the actual file from the project, 53 sheets, dates 2026-02-22 to 2026-05-26)

Column layout (0-based indices):
  col 0  = Order No.
  col 8  = Start Time  (datetime string "DD-MM-YYYY HH:MM")
  col 10 = End Time    (datetime string "DD-MM-YYYY HH:MM")

Logic: a job is active on target_date when
    start_date <= target_date <= end_date
"""

import os
import sys
import unittest
from datetime import date, datetime

# Allow running from the tests/ folder or from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from get_jobs_by_date import (  # noqa: E402
    _find_header_row,
    _jobs_in_sheet,
    _order_no_if_active,
    _parse_str_to_date,
    _to_date,
    get_jobs_by_date,
)

FIXTURE = os.path.join(os.path.dirname(__file__), "..", "data", "sample", "OperationsByDay.xlsx")


class TestGetJobsByDate(unittest.TestCase):
    """Integration tests driven by the real OperationsByDay.xlsx sample file."""

    # ------------------------------------------------------------------
    # Return type
    # ------------------------------------------------------------------

    def test_returns_list(self) -> None:
        result = get_jobs_by_date(FIXTURE, date(2026, 3, 14))
        self.assertIsInstance(result, list)

    # ------------------------------------------------------------------
    # 2026-03-14  — 32 jobs expected
    # ------------------------------------------------------------------

    EXPECTED_2026_03_14 = [
        "J2512-0126",
        "J2512-0198",
        "J2602-0081",
        "J2601-0054",
        "J2601-0075/J2602-0080",
        "J2602-0193",
        "J2512-0153",
        "J2603-0089",
        "J2512-0155/156",
        "J2602-0119",
        "J2511-0176",
        "J2602-0075/J2603-0106",
        "J2602-0190",
        "J2601-0028/J2603-0101",
        "J2602-0113",
        "J2601-0294/295",
        "J2603-0090",
        "J2602-0189",
        "J2602-0146/151",
        "J2601-0276/278/280/J2602-0203.01",
        "J2603-0087",
        "P205115-00",
        "J2512-0192/193",
        "J2603-0072/97",
        "J2602-0187",
        "J2603-0115",
        "J2603-0030",
        "J2512-0199/200",
        "J2602-0144",
        "J2603-0109",
        "J2601-0079/J2603-0068",
        "J2602-0163",
    ]

    def test_count_on_2026_03_14(self) -> None:
        result = get_jobs_by_date(FIXTURE, date(2026, 3, 14))
        self.assertEqual(len(result), 32)

    def test_jobs_active_on_2026_03_14(self) -> None:
        result = get_jobs_by_date(FIXTURE, date(2026, 3, 14))
        self.assertEqual(sorted(result), sorted(self.EXPECTED_2026_03_14))

    def test_scan_order_on_2026_03_14(self) -> None:
        """Jobs must come out in sheet-scan order, not sorted."""
        result = get_jobs_by_date(FIXTURE, date(2026, 3, 14))
        self.assertEqual(result, self.EXPECTED_2026_03_14)

    # ------------------------------------------------------------------
    # Boundary: job starts exactly on target date (Sheet20 → J2603-0115)
    # ------------------------------------------------------------------

    def test_job_starting_on_target_date_included(self) -> None:
        # J2603-0115: 14-03-2026 09:22 → 14-03-2026 12:18  (same-day job)
        result = get_jobs_by_date(FIXTURE, date(2026, 3, 14))
        self.assertIn("J2603-0115", result)

    # ------------------------------------------------------------------
    # Boundary: job ends exactly on target date (Sheet16 → J2602-0119)
    # ------------------------------------------------------------------

    def test_job_ending_on_target_date_included(self) -> None:
        # J2602-0119: 10-03-2026 → 14-03-2026
        result = get_jobs_by_date(FIXTURE, date(2026, 3, 14))
        self.assertIn("J2602-0119", result)

    # ------------------------------------------------------------------
    # Boundary: job that ends the day before must NOT appear
    # ------------------------------------------------------------------

    def test_job_ended_before_target_excluded(self) -> None:
        # J2601-0202: 02-03-2026 → 04-03-2026  (finished well before Mar 14)
        result = get_jobs_by_date(FIXTURE, date(2026, 3, 14))
        self.assertNotIn("J2601-0202", result)

    # ------------------------------------------------------------------
    # Boundary: job that starts the day after must NOT appear
    # ------------------------------------------------------------------

    def test_job_starting_after_target_excluded(self) -> None:
        # J2603-0136: 16-03-2026 → 22-03-2026  → must NOT appear on Mar 14
        result = get_jobs_by_date(FIXTURE, date(2026, 3, 14))
        self.assertNotIn("J2603-0136", result)

    # ------------------------------------------------------------------
    # No duplicates across sheets
    # ------------------------------------------------------------------

    def test_no_duplicate_order_numbers(self) -> None:
        result = get_jobs_by_date(FIXTURE, date(2026, 3, 14))
        self.assertEqual(len(result), len(set(result)))

    # ------------------------------------------------------------------
    # Empty result: date before the first sheet
    # ------------------------------------------------------------------

    def test_no_jobs_before_data_range(self) -> None:
        result = get_jobs_by_date(FIXTURE, date(2026, 1, 1))
        self.assertEqual(result, [])

    # ------------------------------------------------------------------
    # 2026-03-17 — 41 jobs expected
    # ------------------------------------------------------------------

    EXPECTED_2026_03_17 = [
        "J2512-0126",
        "J2601-0054",
        "J2601-0075/J2602-0080",
        "J2602-0193",
        "J2512-0153",
        "J2602-0081",
        "J2603-0089",
        "J2512-0155/156",
        "J2511-0176",
        "J2602-0075/J2603-0106",
        "J2601-0028/J2603-0101",
        "J2602-0113",
        "J2601-0276/278/280/J2602-0203.01",
        "J2602-0119",
        "J2601-0294/295",
        "J2512-0192/193",
        "J2602-0187",
        "J2512-0199/200",
        "J2602-0144",
        "J2602-0163",
        "J2512-0206",
        "J2603-0136",
        "J2603-0030",
        "J2602-0020",
        "J2602-0189",
        "J2603-0090",
        "J2602-0190",
        "J2602-0096",
        "J2512-0205",
        "J2603-0092",
        "J2603-0081",
        "J2602-0146/151",
        "J2603-0078",
        "J2603-0109",
        "J2602-0139/J2603-0088",
        "J2603-0116/117",
        "J2601-0071/73/J2602-0202",
        "J2602-0079",
        "J2602-0028",
        "J2603-0082",
        "J2603-0110",
    ]

    def test_count_on_2026_03_17(self) -> None:
        result = get_jobs_by_date(FIXTURE, date(2026, 3, 17))
        self.assertEqual(len(result), 41)

    def test_jobs_active_on_2026_03_17(self) -> None:
        result = get_jobs_by_date(FIXTURE, date(2026, 3, 17))
        self.assertEqual(sorted(result), sorted(self.EXPECTED_2026_03_17))


class TestHelpers(unittest.TestCase):
    """Unit tests for internal helpers — ensures 100 % branch coverage."""

    # ------------------------------------------------------------------
    # _parse_str_to_date
    # ------------------------------------------------------------------

    def test_parse_str_dmy_with_time(self) -> None:
        self.assertEqual(_parse_str_to_date("14-03-2026 08:00"), date(2026, 3, 14))

    def test_parse_str_dmy(self) -> None:
        self.assertEqual(_parse_str_to_date("14-03-2026"), date(2026, 3, 14))

    def test_parse_str_ymd_with_time(self) -> None:
        self.assertEqual(_parse_str_to_date("2026-03-14 08:00:00"), date(2026, 3, 14))

    def test_parse_str_ymd(self) -> None:
        self.assertEqual(_parse_str_to_date("2026-03-14"), date(2026, 3, 14))

    def test_parse_str_invalid_returns_none(self) -> None:
        self.assertIsNone(_parse_str_to_date("not-a-date"))

    # ------------------------------------------------------------------
    # _to_date
    # ------------------------------------------------------------------

    def test_to_date_none(self) -> None:
        self.assertIsNone(_to_date(None))

    def test_to_date_datetime(self) -> None:
        dt = datetime(2026, 3, 14, 8, 0)
        self.assertEqual(_to_date(dt), date(2026, 3, 14))

    def test_to_date_bare_date(self) -> None:
        d = date(2026, 3, 14)
        self.assertEqual(_to_date(d), d)

    def test_to_date_string(self) -> None:
        self.assertEqual(_to_date("14-03-2026 08:00"), date(2026, 3, 14))

    def test_to_date_unsupported_type(self) -> None:
        self.assertIsNone(_to_date(42))  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # _find_header_row
    # ------------------------------------------------------------------

    def test_find_header_row_not_found(self) -> None:
        rows = [("random", "data"), ("no", "header")]
        self.assertIsNone(_find_header_row(rows))

    def test_find_header_row_found(self) -> None:
        rows = [("something", None), ("Order No.", "Product")]
        self.assertEqual(_find_header_row(rows), 1)

    # ------------------------------------------------------------------
    # _order_no_if_active
    # ------------------------------------------------------------------

    def test_order_no_if_active_none_row(self) -> None:
        self.assertIsNone(_order_no_if_active(None, date(2026, 3, 14)))

    def test_order_no_if_active_null_order_col(self) -> None:
        row = [None] + [None] * 11
        self.assertIsNone(_order_no_if_active(row, date(2026, 3, 14)))

    def test_order_no_if_active_missing_dates(self) -> None:
        row = ["J-001"] + [None] * 11
        self.assertIsNone(_order_no_if_active(row, date(2026, 3, 14)))

    def test_order_no_if_active_outside_range(self) -> None:
        row = ["J-001"] + [None] * 7
        row += [datetime(2026, 3, 1), None, datetime(2026, 3, 5), None]
        self.assertIsNone(_order_no_if_active(row, date(2026, 3, 14)))

    # ------------------------------------------------------------------
    # _jobs_in_sheet
    # ------------------------------------------------------------------

    def test_jobs_in_sheet_no_header(self) -> None:
        import openpyxl

        wb = openpyxl.Workbook()
        ws = wb.active
        ws["A1"] = "no header row here"  # type: ignore[index]
        self.assertEqual(_jobs_in_sheet(ws, date(2026, 3, 14)), [])


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
