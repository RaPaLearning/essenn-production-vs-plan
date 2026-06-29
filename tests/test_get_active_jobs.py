import os
import sys
import tempfile
import unittest

import pandas as pd


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import MagicMock, patch

from get_active_jobs import _parse_datetime, _process_row  # type: ignore[reportPrivateUsage]
from write_active_jobs import export_active_jobs

FIXTURE = "tests/fixtures/test_operations.xlsx"


class TestGetActiveJobs(unittest.TestCase):
    # --- edge cases for 100% coverage via public API ---

    def test_edge_cases_in_temp_file(self) -> None:
        data: list[list[object]] = []
        for _ in range(5):
            data.append([None] * 12)  # Headers

        # Row 5: Missing order
        r1: list[object] = [None] * 12
        r1[8] = "10/03/2026"
        r1[10] = "15/03/2026"
        data.append(r1)

        # Row 6: Missing start
        r2: list[object] = [None] * 12
        r2[0] = "J001"
        r2[10] = "15/03/2026"
        data.append(r2)

        # Row 7: Unparseable date
        r3: list[object] = [None] * 12
        r3[0] = "J002"
        r3[8] = "bad-date"
        r3[10] = "15/03/2026"
        data.append(r3)

        df1 = pd.DataFrame(data)
        df2 = pd.DataFrame([[1, 2, 3]])  # Less than 6 rows

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path: str = tmp.name

        out_path: str = ""
        try:
            with pd.ExcelWriter(tmp_path) as writer:  # type: ignore[reportUnknownVariableType]
                df1.to_excel(writer, sheet_name="Sheet1", index=False, header=False)  # type: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                df2.to_excel(writer, sheet_name="Sheet2", index=False, header=False)  # type: ignore[reportUnknownMemberType, reportUnknownArgumentType]

            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as out:
                out_path = out.name
            export_active_jobs(tmp_path, "2026-03-12", out_path)
            result: pd.DataFrame = pd.read_excel(out_path, header=5)  # type: ignore[reportUnknownMemberType]
            # No active jobs: 5 rows (sub-header, fallback, blanks, sign)
            self.assertEqual(len(result), 5)
            self.assertEqual(result.iloc[1]["MACHINE"], "No active jobs scheduled for this shift")
        finally:
            os.remove(tmp_path)
            os.remove(out_path)

    # --- export_active_jobs ---

    def test_export_creates_file_with_jobs(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as active_jobs_file:
            active_jobs_path: str = active_jobs_file.name

        try:
            export_active_jobs(FIXTURE, "2026-03-10", active_jobs_path)
            result: pd.DataFrame = pd.read_excel(active_jobs_path, header=5)  # type: ignore[reportUnknownMemberType]
            self.assertIn("JOB ORDER No", result.columns)  # type: ignore[reportUnknownMemberType]
            self.assertIn("MACHINE", result.columns)  # type: ignore[reportUnknownMemberType]
            self.assertGreater(len(result), 0)
        finally:
            os.remove(active_jobs_path)

    def test_export_empty_date_creates_empty_file(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as active_jobs_file:
            active_jobs_path: str = active_jobs_file.name

        try:
            export_active_jobs(FIXTURE, "2026-01-01", active_jobs_path)
            result: pd.DataFrame = pd.read_excel(active_jobs_path, header=5)  # type: ignore[reportUnknownMemberType]
            self.assertEqual(len(result), 5)
            self.assertEqual(result.iloc[1]["MACHINE"], "No active jobs scheduled for this shift")
        finally:
            os.remove(active_jobs_path)

    @patch("write_active_jobs.load_machine_types")
    def test_export_fallback_when_machine_list_missing(self, mock_load: MagicMock) -> None:
        """Cover the exception branch in export_active_jobs when Machine List sheet is missing."""
        mock_load.side_effect = Exception("Worksheet named 'Machine list' not found")
        
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as active_jobs_file:
            active_jobs_path: str = active_jobs_file.name

        try:
            # We must pass masterlist_path to trigger the loading attempt
            # Since load_cycle_times works, we need a valid xlsx for it. We'll mock it too
            # to keep the test simple.
            with patch("write_active_jobs.load_cycle_times") as mock_cycle:
                mock_cycle.return_value = {}
                export_active_jobs(FIXTURE, "2026-03-10", active_jobs_path, masterlist_path="dummy.xlsx")
            
            # The exception should be caught and passed, allowing export to finish
            result: pd.DataFrame = pd.read_excel(active_jobs_path, header=5)  # type: ignore[reportUnknownMemberType]
            self.assertGreater(len(result), 0)
        finally:
            os.remove(active_jobs_path)

    # --- _parse_datetime branch coverage (no pragma: no cover) ---

    def test_parse_datetime_returns_none_for_nan(self) -> None:
        """Cover the pd.isna branch in _parse_datetime."""
        row = pd.Series([None] * 12)
        result = _parse_datetime(row, 0)
        self.assertIsNone(result)

    def test_parse_datetime_returns_none_for_bad_value(self) -> None:
        """Cover the Exception branch in _parse_datetime."""
        row = pd.Series(["not-a-date"] * 12)
        result = _parse_datetime(row, 0)
        self.assertIsNone(result)

    @patch("get_active_jobs._parse_datetime")
    def test_process_row_parse_datetime_fails(self, mock_parse_datetime: MagicMock) -> None:
        """Cover the start_dt is None or end_dt is None check in _process_row."""
        # Setup row with valid dates so _parse_date passes
        import datetime
        row = pd.Series([None] * 12)
        row.iloc[0] = "J001"
        row.iloc[8] = "10/03/2026"
        row.iloc[10] = "15/03/2026"
        target = datetime.date(2026, 3, 12)

        # But force _parse_datetime to return None
        mock_parse_datetime.return_value = None

        records, anomalies = _process_row(row, target)
        self.assertEqual(records, [])
        self.assertEqual(anomalies, [])
