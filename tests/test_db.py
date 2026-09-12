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

    @patch("db.upload_masterlist.supabase")
    @patch("pandas.read_excel")
    def test_upload_masterlist(self, mock_read_excel: Any, mock_supabase: Any) -> None:
        mock_read_excel.return_value = self._create_mock_df()
        mock_res = MagicMock()
        mock_res.data = [1]
        mock_supabase.table().insert().execute.return_value = mock_res  # type: ignore[reportUnknownMemberType]
        uploaded = upload_masterlist("fake.xlsx")
        self.assertEqual(uploaded, 1)

    @patch("db.upload_masterlist.supabase", None)
    def test_upload_no_client(self) -> None:
        result = upload_masterlist("fake.xlsx")
        self.assertEqual(result, 0)

    @patch("db.upload_masterlist.supabase")
    @patch("pandas.read_excel")
    def test_upload_with_nan_ct_sec(self, mock_read_excel: Any, mock_supabase: Any) -> None:
        import numpy as np

        mock_read_excel.return_value = self._create_mock_df(np.nan)
        mock_res = MagicMock()
        mock_res.data = [1]
        mock_supabase.table().insert().execute.return_value = mock_res  # type: ignore[reportUnknownMemberType]
        uploaded = upload_masterlist("fake.xlsx")
        self.assertEqual(uploaded, 1)

    @patch("db.upload_masterlist.supabase")
    @patch("pandas.read_excel")
    def test_upload_insert_error(self, mock_read_excel: Any, mock_supabase: Any) -> None:
        mock_read_excel.return_value = self._create_mock_df(10.0)
        mock_supabase.table().insert().execute.side_effect = Exception("db error")  # type: ignore[reportUnknownMemberType]
        result = upload_masterlist("fake.xlsx")
        self.assertEqual(result, 0)

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

    def test_success(self) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch.object(run_migrations, "supabase", MagicMock()):
            with patch.dict(
                os.environ,
                {"SUPABASE_URL": "http://test", "SUPABASE_KEY": "key"},
            ):
                with patch.object(run_migrations.httpx, "post", return_value=mock_resp):
                    run_migrations.run_migrations()

    def test_fallback(self) -> None:
        mock_resp_fail = MagicMock()
        mock_resp_fail.status_code = 404
        mock_resp_ok = MagicMock()
        mock_resp_ok.status_code = 200
        with patch.object(run_migrations, "supabase", MagicMock()):
            with patch.dict(
                os.environ,
                {"SUPABASE_URL": "http://test", "SUPABASE_KEY": "key"},
            ):
                with patch.object(
                    run_migrations.httpx,
                    "post",
                    side_effect=[
                        mock_resp_fail,
                        mock_resp_ok,
                        mock_resp_fail,
                        mock_resp_ok,
                    ],
                ):
                    run_migrations.run_migrations()

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
