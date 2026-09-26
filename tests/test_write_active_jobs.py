import unittest
from typing import Any
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from write_active_jobs import export_active_jobs


class TestWriteActiveJobs(unittest.TestCase):
    @patch("write_active_jobs.load_cycle_times")
    @patch("write_active_jobs.load_machine_types")
    @patch("write_active_jobs.get_active_jobs")
    @patch("write_active_jobs.openpyxl.Workbook")
    @patch("db.save_summaries.save_report_summaries")
    def test_export_supabase_exception(
        self,
        mock_save: Any,
        mock_wb: Any,
        mock_get_active_jobs: Any,
        _mock_machine: Any,
        _mock_cycle: Any,
    ) -> None:
        mock_get_active_jobs.return_value = ([], [])
        mock_save.side_effect = Exception("test error")
        mock_wb_instance = MagicMock()
        mock_wb.return_value = mock_wb_instance

        export_active_jobs("dummy.xlsx", "2026-09-12", "master.xlsx", "machine.xlsx")

        mock_wb.assert_called_once()  # type: ignore[reportUnknownMemberType]

    @patch("write_active_jobs.load_cycle_times")
    @patch("write_active_jobs.load_machine_types")
    @patch("write_active_jobs.get_active_jobs")
    @patch("write_active_jobs.openpyxl.Workbook")
    @patch("db.save_summaries.save_report_summaries")
    def test_export_supabase_success(
        self,
        mock_save: Any,
        mock_wb: Any,
        mock_get_active_jobs: Any,
        _mock_machine: Any,
        _mock_cycle: Any,
    ) -> None:
        mock_get_active_jobs.return_value = ([], [])
        mock_wb_instance = MagicMock()
        mock_wb.return_value = mock_wb_instance

        export_active_jobs("dummy.xlsx", "2026-09-12", "master.xlsx", "machine.xlsx")

        mock_wb.assert_called_once()  # type: ignore[reportUnknownMemberType]
