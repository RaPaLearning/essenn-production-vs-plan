"""Test database functions."""

import os
import unittest
from typing import Any
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.save_summaries import save_report_summaries  # type: ignore[reportUnknownVariableType]
from db.upload_masterlist import upload_masterlist
import run_migrations


class TestSaveSummaries(unittest.TestCase):
    @patch("db.save_summaries.supabase")
    def test_save_report_summaries(self, mock_supabase: Any) -> None:
        rows: list[dict[str, str]] = [
            {
                "Shift": "Shift A",
                "Machine": "M1",
                "Job Order No": "J1",
                "Total QTY": "100",
                "Part No": "P1",
                "Part Name": "N1",
                "Operation": "O1",
                "Plan Qty": "50",
                "OK QTY": "40",
            }
        ]
        save_report_summaries("2026-09-12", rows, [])
        mock_supabase.table.assert_called_with("summaries")  # type: ignore[reportUnknownMemberType]
        mock_supabase.table().insert.assert_called()  # type: ignore[reportUnknownMemberType]

    @patch("db.save_summaries.supabase")
    def test_save_empty_rows(self, mock_supabase: Any) -> None:
        save_report_summaries("2026-09-12", [], [])
        mock_supabase.table.assert_not_called()  # type: ignore[reportUnknownMemberType]

    @patch("db.save_summaries.supabase", None)
    def test_save_no_client(self) -> None:
        save_report_summaries("2026-09-12", [{"Shift": "A"}], [])

    @patch("db.save_summaries.supabase")
    def test_save_non_digit_fields(self, mock_supabase: Any) -> None:
        rows: list[dict[str, str]] = [
            {
                "Shift": "A",
                "Machine": "M1",
                "Job Order No": "J1",
                "Total QTY": "abc",
                "Part No": "P1",
                "Part Name": "N1",
                "Operation": "O1",
                "Plan Qty": "xyz",
                "OK QTY": "nope",
            }
        ]
        save_report_summaries("2026-09-12", rows, [])
        mock_supabase.table.assert_called_with("summaries")  # type: ignore[reportUnknownMemberType]

    @patch("db.save_summaries.supabase")
    def test_save_insert_error(self, mock_supabase: Any) -> None:
        mock_supabase.table().insert().execute.side_effect = Exception("db error")  # type: ignore[reportUnknownMemberType]
        rows: list[dict[str, str]] = [
            {
                "Shift": "A",
                "Machine": "M1",
                "Job Order No": "J1",
                "Part No": "P1",
                "Part Name": "N1",
                "Operation": "O1",
            }
        ]
        save_report_summaries("2026-09-12", rows, [])


class TestUploadMasterlist(unittest.TestCase):
    def _create_mock_df(self, ct_sec: Any = 10.5) -> Any:
        import pandas as pd

        return pd.DataFrame(
            {
                "PART NO.": ["P1"],
                "PART NAME": ["N1"],
                "OPN NO.": ["O1"],
                "OPERATION NAME": ["ON1"],
                "RESOURCE": ["R1"],
                "CT \nSEC": [ct_sec],
                "MACHINE TYPE": ["M1"],
            }
        )

    def _setup_mock_supabase_insert(self, mock_sb: Any, return_data: Any) -> None:
        mock_res = MagicMock()
        mock_res.data = return_data
        mock_sb.table().insert().execute.return_value = mock_res  # type: ignore[reportUnknownMemberType]

    @patch("db.upload_masterlist.supabase")
    @patch("pandas.read_excel")
    def test_upload_masterlist(self, mock_read_excel: Any, mock_supabase: Any) -> None:
        mock_read_excel.return_value = self._create_mock_df()
        self._setup_mock_supabase_insert(mock_supabase, [1])
        self.assertEqual(upload_masterlist("fake.xlsx"), 1)

    @patch("db.upload_masterlist.supabase", None)
    def test_upload_no_client(self) -> None:
        self.assertEqual(upload_masterlist("fake.xlsx"), 0)

    @patch("db.upload_masterlist.supabase")
    @patch("pandas.read_excel")
    def test_upload_with_nan_ct_sec(self, mock_read_excel: Any, mock_supabase: Any) -> None:
        import numpy as np

        mock_read_excel.return_value = self._create_mock_df(np.nan)
        self._setup_mock_supabase_insert(mock_supabase, [{"id": 1}])
        self.assertEqual(upload_masterlist("nan_ct.xlsx"), 1)

    @patch("db.upload_masterlist.supabase")
    @patch("pandas.read_excel")
    def test_upload_insert_error(self, mock_read_excel: Any, mock_supabase: Any) -> None:
        mock_read_excel.return_value = self._create_mock_df(10.0)
        mock_supabase.table().insert().execute.side_effect = Exception("db error")  # type: ignore[reportUnknownMemberType]
        self.assertEqual(upload_masterlist("fake.xlsx"), 0)

    @patch("pandas.read_excel")
    @patch("db.upload_masterlist.supabase")
    def test_main_cli(self, mock_supabase: Any, mock_read_excel: Any) -> None:
        mock_read_excel.return_value = self._create_mock_df()
        with patch.object(sys, "argv", ["upload_masterlist.py", "test.xlsx"]):
            import runpy

            runpy.run_module("db.upload_masterlist", run_name="__main__")

    def test_main_cli_no_args(self) -> None:
        with patch.object(sys, "argv", ["upload_masterlist.py"]):
            import runpy

            runpy.run_module("db.upload_masterlist", run_name="__main__")


class TestRunMigrations(unittest.TestCase):
    def test_no_client(self) -> None:
        with patch.object(run_migrations, "supabase", None):
            run_migrations.run_migrations()

    def test_no_env_vars(self) -> None:
        with patch.object(run_migrations, "supabase", MagicMock()):
            with patch.dict(os.environ, {}, clear=True):
                run_migrations.run_migrations()

    def _run_with_mock_http(self, post_side_effect: Any) -> None:
        with patch.object(run_migrations, "supabase", MagicMock()):
            with patch.dict(
                os.environ,
                {"SUPABASE_URL": "http://test", "SUPABASE_KEY": "key"},
            ):
                with patch.object(run_migrations.httpx, "post", side_effect=post_side_effect):
                    run_migrations.run_migrations()

    def test_success(self) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        self._run_with_mock_http([mock_resp, mock_resp])

    def test_fallback(self) -> None:
        mock_resp_fail = MagicMock()
        mock_resp_fail.status_code = 404
        mock_resp_ok = MagicMock()
        mock_resp_ok.status_code = 200
        self._run_with_mock_http([mock_resp_fail, mock_resp_ok, mock_resp_fail, mock_resp_ok])

    @patch("httpx.post")
    def test_main_cli(self, mock_httpx_post: Any) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_httpx_post.return_value = mock_resp
        with patch.dict(
            os.environ,
            {"SUPABASE_URL": "http://test", "SUPABASE_KEY": "key"},
        ):
            with patch("db.client.supabase", MagicMock()):
                import runpy

                runpy.run_module("run_migrations", run_name="__main__")


class TestDbClient(unittest.TestCase):
    def test_client_none_without_env(self) -> None:
        """When SUPABASE_URL/KEY are empty, supabase should be None."""
        import importlib

        import db.client

        saved_url = os.environ.pop("SUPABASE_URL", None)
        saved_key = os.environ.pop("SUPABASE_KEY", None)
        try:
            with patch("dotenv.load_dotenv"):
                importlib.reload(db.client)
                self.assertIsNone(db.client.supabase)
        finally:
            if saved_url is not None:
                os.environ["SUPABASE_URL"] = saved_url
            if saved_key is not None:
                os.environ["SUPABASE_KEY"] = saved_key
            importlib.reload(db.client)

    def test_client_created_with_env(self) -> None:
        """When SUPABASE_URL/KEY are set, create_client should be called."""
        import importlib

        import db.client

        saved_url = os.environ.get("SUPABASE_URL")
        saved_key = os.environ.get("SUPABASE_KEY")
        try:
            os.environ["SUPABASE_URL"] = "https://fake.supabase.co"
            os.environ["SUPABASE_KEY"] = "fake-key"
            mock_client = MagicMock()
            with (
                patch("dotenv.load_dotenv"),
                patch("supabase.create_client", return_value=mock_client),
            ):
                importlib.reload(db.client)
                self.assertEqual(db.client.supabase, mock_client)
        finally:
            os.environ.pop("SUPABASE_URL", None)
            os.environ.pop("SUPABASE_KEY", None)
            if saved_url is not None:
                os.environ["SUPABASE_URL"] = saved_url
            if saved_key is not None:
                os.environ["SUPABASE_KEY"] = saved_key
            importlib.reload(db.client)
