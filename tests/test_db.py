"""Test database functions against a real Supabase instance."""

import os
from typing import Any, cast
import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client, Client

from db.save_summaries import save_report_summaries  # type: ignore[reportUnknownVariableType]
from db.upload_masterlist import upload_masterlist, _build_row  # pyright: ignore[reportPrivateUsage]
from db.get_masterlist import get_masterlist
import run_migrations

load_dotenv()


def _get_test_client() -> Client | None:
    """Create a Supabase client pointing at the test project."""
    url = os.environ.get("TEST_SUPABASE_URL", "")
    key = os.environ.get("TEST_SUPABASE_KEY", "")
    if url and key:
        return create_client(url, key)
    return None


def _wipe_table(client: Client, table: str) -> None:
    """Delete all rows from a table in the test database."""
    client.table(table).delete().neq("id", 0).execute()


# ---------------------------------------------------------------------------
# Unit tests — no database needed
# ---------------------------------------------------------------------------


class TestBuildRow(unittest.TestCase):
    """Test the _build_row helper with various inputs."""

    def test_valid_row(self) -> None:
        import pandas as pd

        row = pd.Series(
            {
                "PART NO.": "  P1  ",
                "PART NAME": "  Name1  ",
                "OPN NO.": "O1",
                "OPERATION NAME": "Op1",
                "RESOURCE": "R1",
                "CT \nSEC": 10.5,
                "MACHINE TYPE": "M1",
            }
        )
        result = _build_row(row)
        self.assertEqual(result["part_no"], "P1")
        self.assertEqual(result["part_name"], "Name1")
        self.assertEqual(result["ct_sec"], 10.5)

    def test_nan_ct_sec(self) -> None:
        import pandas as pd
        import numpy as np

        row = pd.Series(
            {
                "PART NO.": "P1",
                "PART NAME": "N1",
                "OPN NO.": "O1",
                "OPERATION NAME": "ON1",
                "RESOURCE": "R1",
                "CT \nSEC": np.nan,
                "MACHINE TYPE": "M1",
            }
        )
        result = _build_row(row)
        self.assertIsNone(result["ct_sec"])

    def test_non_numeric_ct_sec(self) -> None:
        import pandas as pd

        row = pd.Series(
            {
                "PART NO.": "P1",
                "PART NAME": "N1",
                "OPN NO.": "O1",
                "OPERATION NAME": "ON1",
                "RESOURCE": "R1",
                "CT \nSEC": "abc",
                "MACHINE TYPE": "M1",
            }
        )
        result = _build_row(row)
        self.assertIsNone(result["ct_sec"])


class TestParseInt(unittest.TestCase):
    """Test the _parse_int helper."""

    def test_digit(self) -> None:
        from db.save_summaries import _parse_int  # pyright: ignore[reportPrivateUsage]

        self.assertEqual(_parse_int({"k": "42"}, "k"), 42)  # pyright: ignore[reportPrivateUsage]

    def test_non_digit(self) -> None:
        from db.save_summaries import _parse_int  # pyright: ignore[reportPrivateUsage]

        self.assertIsNone(_parse_int({"k": "abc"}, "k"))  # pyright: ignore[reportPrivateUsage]

    def test_missing_key(self) -> None:
        from db.save_summaries import _parse_int  # pyright: ignore[reportPrivateUsage]

        self.assertIsNone(_parse_int({}, "k"))  # pyright: ignore[reportPrivateUsage]


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


# ---------------------------------------------------------------------------
# Integration tests — run against real test Supabase
# ---------------------------------------------------------------------------

_test_client = cast(Any, _get_test_client())
_skip_reason = "TEST_SUPABASE_URL/KEY not set"


@unittest.skipUnless(_test_client, _skip_reason)
class TestTablesExist(unittest.TestCase):
    """Verify that the expected tables exist in the test database."""

    def test_masterlist_table_exists(self) -> None:
        res = _test_client.table("masterlist").select("*").limit(1).execute()
        self.assertIsInstance(res.data, list)

    def test_summaries_table_exists(self) -> None:
        res = _test_client.table("summaries").select("*").limit(1).execute()
        self.assertIsInstance(res.data, list)


@unittest.skipUnless(_test_client, _skip_reason)
class TestUploadMasterlistIntegration(unittest.TestCase):
    """Test uploading masterlist data to a real database."""

    def setUp(self) -> None:
        _wipe_table(_test_client, "masterlist")

    def _fetch_masterlist_rows(self) -> list[dict[str, Any]]:
        res = _test_client.table("masterlist").select("*").execute()
        return [cast(dict[str, Any], r) for r in res.data]

    def test_upload_inserts_real_data(self) -> None:
        # Point the module's client at our test database
        with patch("db.upload_masterlist.supabase", _test_client):
            import pandas as pd

            df = pd.DataFrame(
                {
                    "PART NO.": ["P1"],
                    "PART NAME": ["Name1"],
                    "OPN NO.": ["O1"],
                    "OPERATION NAME": ["Op1"],
                    "RESOURCE": ["R1"],
                    "CT \nSEC": [10.5],
                    "MACHINE TYPE": ["M1"],
                }
            )
            with patch("pandas.read_excel", return_value=df):
                count = upload_masterlist("fake.xlsx")

        self.assertEqual(count, 1)
        # Read back from DB and verify
        rows = self._fetch_masterlist_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["part_no"], "P1")
        self.assertEqual(rows[0]["part_name"], "Name1")
        self.assertEqual(float(rows[0]["ct_sec"]), 10.5)

    def test_upload_replaces_old_data(self) -> None:
        """Uploading again should wipe old rows (handles deleted Excel rows)."""
        import pandas as pd

        df1 = pd.DataFrame(
            {
                "PART NO.": ["P1", "P2"],
                "PART NAME": ["N1", "N2"],
                "OPN NO.": ["O1", "O2"],
                "OPERATION NAME": ["ON1", "ON2"],
                "RESOURCE": ["R1", "R2"],
                "CT \nSEC": [10.0, 20.0],
                "MACHINE TYPE": ["M1", "M2"],
            }
        )
        # First upload: 2 rows
        with patch("db.upload_masterlist.supabase", _test_client):
            with patch("pandas.read_excel", return_value=df1):
                upload_masterlist("fake.xlsx")

        # Second upload: only 1 row (P2 "deleted" from Excel)
        df2 = df1.iloc[:1]
        with patch("db.upload_masterlist.supabase", _test_client):
            with patch("pandas.read_excel", return_value=df2):
                upload_masterlist("fake.xlsx")

        rows = self._fetch_masterlist_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["part_no"], "P1")


@unittest.skipUnless(_test_client, _skip_reason)
class TestSaveSummariesIntegration(unittest.TestCase):
    """Test saving summaries to a real database."""

    def setUp(self) -> None:
        _wipe_table(_test_client, "summaries")

    def _save_and_fetch(self, rows: list[dict[str, str]]) -> list[dict[str, Any]]:
        with patch("db.save_summaries.supabase", _test_client):
            save_report_summaries("2026-10-04", rows, [])
        return cast(
            list[dict[str, Any]], _test_client.table("summaries").select("*").execute().data
        )

    def test_save_inserts_real_data(self) -> None:
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
        data = self._save_and_fetch(rows)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["shift"], "Shift A")
        self.assertEqual(data[0]["machine"], "M1")
        self.assertEqual(data[0]["ok_qty"], 40)

    def test_save_non_digit_fields(self) -> None:
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
        data = self._save_and_fetch(rows)
        self.assertEqual(len(data), 1)
        self.assertIsNone(data[0]["total_qty"])
        self.assertIsNone(data[0]["ok_qty"])


@unittest.skipUnless(_test_client, _skip_reason)
class TestGetMasterlistIntegration(unittest.TestCase):
    """Test retrieving masterlist from a real database."""

    def setUp(self) -> None:
        _wipe_table(_test_client, "masterlist")

    def test_get_returns_data(self) -> None:
        # Insert a row directly
        _test_client.table("masterlist").insert(
            {
                "part_no": "P1",
                "part_name": "N1",
                "operation_no": "O1",
                "operation_name": "ON1",
                "resource": "R1",
                "ct_sec": 10.5,
                "machine_type": "M1",
            }
        ).execute()

        with patch("db.get_masterlist.supabase", _test_client):
            df = get_masterlist()

        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["part_no"], "P1")

    def test_get_empty_table(self) -> None:
        with patch("db.get_masterlist.supabase", _test_client):
            df = get_masterlist()
        self.assertEqual(len(df), 0)


# ---------------------------------------------------------------------------
# Coverage-only tests for edge cases and CLI entry points
# ---------------------------------------------------------------------------


class TestUploadEdgeCases(unittest.TestCase):
    @patch("db.upload_masterlist.supabase", None)
    def test_upload_no_client(self) -> None:
        self.assertEqual(upload_masterlist("fake.xlsx"), 0)

    @patch("db.upload_masterlist.supabase")
    def test_upload_error(self, mock_supabase: Any) -> None:
        mock_supabase.table().delete().neq().execute.side_effect = Exception("db error")
        import pandas as pd

        df = pd.DataFrame({"PART NO.": ["P1"]})
        with patch("pandas.read_excel", return_value=df):
            self.assertEqual(upload_masterlist("fake.xlsx"), 0)

    def test_main_cli_no_args(self) -> None:
        with patch.object(sys, "argv", ["upload_masterlist.py"]):
            import runpy

            runpy.run_module("db.upload_masterlist", run_name="__main__")


class TestSaveEdgeCases(unittest.TestCase):
    @patch("db.save_summaries.supabase", None)
    def test_save_no_client(self) -> None:
        save_report_summaries("2026-10-04", [{"Shift": "A"}], [])

    @patch("db.save_summaries.supabase")
    def test_save_empty_rows(self, mock_supabase: Any) -> None:
        save_report_summaries("2026-10-04", [], [])
        mock_supabase.table.assert_not_called()  # type: ignore[reportUnknownMemberType]

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
        save_report_summaries("2026-10-04", rows, [])


class TestGetMasterlistEdgeCases(unittest.TestCase):
    @patch("db.get_masterlist.supabase", None)
    def test_get_no_client(self) -> None:
        df = get_masterlist()
        self.assertEqual(len(df), 0)

    @patch("db.get_masterlist.supabase")
    def test_get_error(self, mock_supabase: Any) -> None:
        mock_supabase.table().select().execute.side_effect = Exception("db error")  # type: ignore[reportUnknownMemberType]
        df = get_masterlist()
        self.assertEqual(len(df), 0)


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
        num_files = len(list(Path("migrations").glob("*.sql")))
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        self._run_with_mock_http([mock_resp] * num_files)

    def test_fallback(self) -> None:
        num_files = len(list(Path("migrations").glob("*.sql")))
        mock_resp_fail = MagicMock()
        mock_resp_fail.status_code = 404
        mock_resp_ok = MagicMock()
        mock_resp_ok.status_code = 200
        side_effect = [mock_resp_fail, mock_resp_ok] * num_files
        self._run_with_mock_http(side_effect)

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

    @patch("supabase.create_client")
    @patch("tests.test_db.create_client")
    def test_get_test_client_with_env(
        self, _mock_create2: MagicMock, _mock_create1: MagicMock
    ) -> None:
        with patch.dict(
            os.environ, {"TEST_SUPABASE_URL": "http://test", "TEST_SUPABASE_KEY": "key"}
        ):
            _get_test_client()
        with patch.dict(os.environ, {"TEST_SUPABASE_URL": "", "TEST_SUPABASE_KEY": ""}, clear=True):
            self.assertIsNone(_get_test_client())
