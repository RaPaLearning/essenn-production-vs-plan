"""Unit tests for db/pg_masterlist.py and db/upload_all_masterlists.py."""

import unittest
from unittest.mock import MagicMock, patch
import os
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.pg_masterlist import (
    time_to_seconds,
    _clean_op_no,  # pyright: ignore[reportPrivateUsage]
    parse_masterlist_excel,
    get_connection,
    ensure_schema,
    create_rows,
    read_rows,
    count_rows,
    update_row,
    delete_row,
    _demo_crud,  # pyright: ignore[reportPrivateUsage]
    main as pg_main,
)
from db.upload_all_masterlists import (
    clean_str,
    clean_int,
    clean_op_no as u_clean_op_no,
    get_connection as u_get_connection,
    apply_migrations,
    upload_main_sheet,
    upload_machine_list,
    upload_template_sheet,
    main as upload_all_main,
)


class TestPgMasterlistHelpers(unittest.TestCase):
    def test_time_to_seconds(self) -> None:
        self.assertEqual(time_to_seconds("0 Hours 20 Mins"), 1200.0)
        self.assertEqual(time_to_seconds("1 Hours 02.5000 Mins"), 3750.0)
        self.assertEqual(time_to_seconds("5.0"), 300.0)
        self.assertIsNone(time_to_seconds(None))
        self.assertIsNone(time_to_seconds("unspecified"))
        self.assertIsNone(time_to_seconds("invalid text"))

    def test_clean_op_no(self) -> None:
        self.assertEqual(_clean_op_no(10.0), "10")
        self.assertEqual(_clean_op_no(" 20 "), "20")

    def test_clean_str_and_int(self) -> None:
        self.assertEqual(clean_str("  hello  "), "hello")
        self.assertIsNone(clean_str("   "))
        self.assertIsNone(clean_str(None))

        self.assertEqual(clean_int(42.0), 42)
        self.assertEqual(clean_int("100"), 100)
        self.assertIsNone(clean_int("abc"))
        self.assertIsNone(clean_int(None))

        self.assertEqual(u_clean_op_no(10.0), "10")
        self.assertIsNone(u_clean_op_no("  "))


class TestPgMasterlistFunctions(unittest.TestCase):
    @patch("pandas.read_excel")
    def test_parse_masterlist_excel(self, mock_read_excel: MagicMock) -> None:
        df = pd.DataFrame(
            {
                "Part No.": ["P1", None],
                "Product": ["Name1", None],
                "Op. No.": [10.0, 20.0],
                "Operation Name": ["Op1", "Op2"],
                "Setup Time": ["0 Hours 10 Mins", "0 Hours 0 Mins"],
                "Op. Time per Item": ["0 Hours 01 Mins", "0 Hours 02 Mins"],
            }
        )
        mock_read_excel.return_value = df
        rows = parse_masterlist_excel("fake.xls")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["part_no"], "P1")
        self.assertEqual(rows[1]["part_no"], "P1")  # forward-filled

    @patch.dict(os.environ, {}, clear=True)
    def test_get_connection_missing_url(self) -> None:
        with self.assertRaises(RuntimeError):
            get_connection()

        with self.assertRaises(RuntimeError):
            u_get_connection()

    @patch("db.pg_masterlist.psycopg.connect")
    @patch.dict(os.environ, {"DATABASE_URL": "postgresql://fake"}, clear=True)
    def test_get_connection_success(self, mock_connect: MagicMock) -> None:
        get_connection()
        mock_connect.assert_called_once_with("postgresql://fake", connect_timeout=15)

    def test_ensure_schema(self) -> None:
        mock_conn = MagicMock()
        ensure_schema(mock_conn)
        self.assertTrue(mock_conn.commit.called)

    def test_crud_operations(self) -> None:
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_conn.transaction.return_value.__enter__.return_value = MagicMock()

        # create_rows
        count = create_rows(mock_conn, [{"part_no": "P1"}], replace=True)
        self.assertEqual(count, 1)

        # read_rows
        mock_cur.fetchall.return_value = [{"id": 1, "part_no": "P1"}]
        rows = read_rows(mock_conn, part_no="P1", limit=10)
        self.assertEqual(len(rows), 1)

        # count_rows
        mock_cur.fetchone.return_value = (5,)
        self.assertEqual(count_rows(mock_conn), 5)

        # update_row
        mock_cur.rowcount = 1
        res = update_row(mock_conn, 1, part_no="P2")
        self.assertEqual(res, 1)

        self.assertEqual(update_row(mock_conn, 1), 0)

        with self.assertRaises(ValueError):
            update_row(mock_conn, 1, invalid_col="x")

        # delete_row
        self.assertEqual(delete_row(mock_conn, 1), 1)

    def test_demo_crud(self) -> None:
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_conn.transaction.return_value.__enter__.return_value = MagicMock()
        mock_cur.fetchall.side_effect = [
            [{"id": 1, "part_no": "__DEMO__"}],
            [{"id": 1, "part_no": "__DEMO__"}],
            [],
        ]

        _demo_crud(mock_conn)

    @patch("db.pg_masterlist.parse_masterlist_excel")
    @patch("db.pg_masterlist.get_connection")
    @patch("db.pg_masterlist.ensure_schema")
    @patch("db.pg_masterlist.create_rows")
    @patch("db.pg_masterlist.count_rows")
    @patch("db.pg_masterlist._demo_crud")
    def test_pg_main(
        self,
        mock_demo_crud: MagicMock,
        mock_count: MagicMock,
        mock_create: MagicMock,
        _mock_ensure: MagicMock,
        _mock_get_conn: MagicMock,
        mock_parse: MagicMock,
    ) -> None:
        mock_parse.return_value = [{"part_no": "P1"}]
        mock_create.return_value = 1
        mock_count.return_value = 1

        pg_main(["pg_masterlist.py"])  # prints usage
        pg_main(["pg_masterlist.py", "fake.xls", "--demo-crud"])
        self.assertTrue(mock_demo_crud.called)


class TestUploadAllMasterlists(unittest.TestCase):
    def test_apply_migrations(self) -> None:
        mock_conn = MagicMock()
        apply_migrations(mock_conn)
        self.assertTrue(mock_conn.commit.called)

    def test_upload_sheets(self) -> None:
        mock_conn = MagicMock()
        mock_xl = MagicMock()
        mock_xl.sheet_names = ["As on 16-05-2026", "Machine list", "Templet"]

        # Main sheet
        df_main = pd.DataFrame(
            {
                "Part No.": ["P1"],
                "Product": ["Name1"],
                "Op. No.": [10.0],
                "Operation Name": ["Op1"],
                "Setup Time": ["0 Hours 10 Mins"],
                "Op. Time per Item": ["0 Hours 01 Mins"],
            }
        )
        # Machine list
        df_machine = pd.DataFrame(
            [
                [None] * 5,
                [None] * 5,
                [None] * 5,
                [None] * 5,
                [None] * 5,
                [None] * 5,
                [None, 1.0, "ACE COLT", "Turning", "2axis Small"],
            ]
        )
        # Templet
        df_template = pd.DataFrame(
            {
                "SL No": [1.0],
                "Part No.": ["P1"],
                "Product": ["Name1"],
                "Op. No.": [10.0],
                "Operation Name": ["Op1"],
                "Setup Time": ["0 Hours 10 Mins"],
                "Op. Time per Item": ["0 Hours 01 Mins"],
                "Resource": ["R1"],
            }
        )

        def mock_parse(sheet_name: str, **_kwargs: object) -> pd.DataFrame:
            if sheet_name == "As on 16-05-2026":
                return df_main
            if sheet_name == "Machine list":
                return df_machine
            return df_template

        mock_xl.parse.side_effect = mock_parse

        self.assertEqual(upload_main_sheet(mock_conn, mock_xl), 1)
        self.assertEqual(upload_machine_list(mock_conn, mock_xl), 1)
        self.assertEqual(upload_template_sheet(mock_conn, mock_xl), 1)

    @patch("db.upload_all_masterlists.pd.ExcelFile")
    @patch("db.upload_all_masterlists.get_connection")
    @patch("db.upload_all_masterlists.apply_migrations")
    @patch("db.upload_all_masterlists.upload_main_sheet")
    @patch("db.upload_all_masterlists.upload_machine_list")
    @patch("db.upload_all_masterlists.upload_template_sheet")
    def test_upload_all_main(
        self,
        _mock_templ: MagicMock,
        _mock_mach: MagicMock,
        mock_main_sheet: MagicMock,
        _mock_apply: MagicMock,
        mock_conn: MagicMock,
        mock_excel: MagicMock,
    ) -> None:
        mock_xl = MagicMock()
        mock_xl.sheet_names = ["As on 16-05-2026", "Machine list", "Templet"]
        mock_excel.return_value = mock_xl

        upload_all_main("fake.xls")
        mock_main_sheet.assert_called_once()

    def test_edge_cases_and_cleaners(self) -> None:
        import numpy as np
        from db.upload_all_masterlists import time_to_seconds as u_time_to_seconds

        self.assertIsNone(u_time_to_seconds(np.nan))
        self.assertIsNone(u_time_to_seconds("none"))
        self.assertIsNone(u_time_to_seconds("nan"))
        self.assertIsNone(u_time_to_seconds(""))
        self.assertIsNone(u_time_to_seconds("invalid"))

        self.assertIsNone(clean_str(np.nan))
        self.assertIsNone(clean_int(np.nan))
        self.assertIsNone(u_clean_op_no(np.nan))

        # Test upload_main_sheet and upload_machine_list with empty/invalid rows
        mock_conn = MagicMock()
        mock_xl = MagicMock()

        df_main_empty = pd.DataFrame(
            {
                "Part No.": [None, "P1"],
                "Product": [None, "Name1"],
                "Op. No.": [None, 10.0],
                "Operation Name": [None, "Op1"],
                "Setup Time": [None, "0 Hours 10 Mins"],
                "Op. Time per Item": [None, "0 Hours 01 Mins"],
            }
        )
        df_machine_empty = pd.DataFrame(
            [[None] * 5] * 6
            + [
                [None, 1.0, None, "Turning", "2axis"],  # Machine is None -> continue
                [None, 2.0, "ACE COLT", "Turning", "2axis"],  # Valid machine -> rows.append
            ]
        )

        def mock_parse(sheet_name: str, **_kwargs: object) -> pd.DataFrame:
            if sheet_name == "As on 16-05-2026":
                return df_main_empty
            return df_machine_empty

        mock_xl.parse.side_effect = mock_parse
        self.assertEqual(upload_main_sheet(mock_conn, mock_xl), 1)
        self.assertEqual(upload_machine_list(mock_conn, mock_xl), 1)

    @patch("db.pg_masterlist.psycopg", None)
    @patch("db.upload_all_masterlists.psycopg", None)
    def test_missing_psycopg(self) -> None:
        with self.assertRaises(RuntimeError):
            get_connection()
        with self.assertRaises(RuntimeError):
            u_get_connection()

    @patch("pandas.read_excel")
    def test_parse_masterlist_excel_empty_rows(self, mock_read_excel: MagicMock) -> None:
        df = pd.DataFrame(
            {
                "Part No.": [None, "P1"],
                "Product": [None, "Prod1"],
                "Op. No.": [10.0, 20.0],
                "Operation Name": ["Op1", None],
                "Setup Time": ["0 Hours 10 Mins", "0 Hours 0 Mins"],
                "Op. Time per Item": ["0 Hours 01 Mins", "0 Hours 02 Mins"],
            }
        )
        mock_read_excel.return_value = df
        rows = parse_masterlist_excel("fake.xls")
        self.assertEqual(len(rows), 0)

    @patch("db.upload_all_masterlists.pd.ExcelFile")
    @patch("db.upload_all_masterlists.get_connection")
    @patch("db.upload_all_masterlists.apply_migrations")
    @patch("db.upload_all_masterlists.upload_main_sheet")
    @patch("db.upload_all_masterlists.upload_machine_list")
    @patch("db.upload_all_masterlists.upload_template_sheet")
    def test_upload_all_cli_entrypoint(self, *_mocks: MagicMock) -> None:
        import runpy

        with patch.object(sys, "argv", ["upload_all_masterlists.py"]):
            runpy.run_module("db.upload_all_masterlists", run_name="__main__")

    @patch("pandas.read_excel")
    @patch("db.pg_masterlist.get_connection")
    @patch("db.pg_masterlist.ensure_schema")
    @patch("db.pg_masterlist.create_rows")
    @patch("db.pg_masterlist.count_rows")
    def test_pg_masterlist_cli_entrypoint(
        self,
        mock_count: MagicMock,
        mock_create: MagicMock,
        _mock_ensure: MagicMock,
        mock_conn: MagicMock,
        mock_read: MagicMock,
    ) -> None:
        import runpy

        mock_read.return_value = pd.DataFrame(
            {
                "Part No.": ["P1"],
                "Product": ["Prod1"],
                "Op. No.": [10.0],
                "Operation Name": ["Op1"],
                "Setup Time": ["0 Hours 10 Mins"],
                "Op. Time per Item": ["0 Hours 01 Mins"],
            }
        )
        with patch.object(sys, "argv", ["pg_masterlist.py", "fake.xls"]):
            runpy.run_module("db.pg_masterlist", run_name="__main__")

    @patch("pandas.read_excel")
    @patch("db.upload_masterlist.supabase")
    def test_upload_masterlist_cli_entrypoint(
        self, mock_supabase: MagicMock, mock_read: MagicMock
    ) -> None:
        import runpy

        mock_read.return_value = pd.DataFrame(
            {"Part No.": ["P1"], "Product": ["Prod1"], "Op. No.": [10.0], "Operation Name": ["Op1"]}
        )
        with patch.object(sys, "argv", ["upload_masterlist.py", "fake.xls"]):
            runpy.run_module("db.upload_masterlist", run_name="__main__")
