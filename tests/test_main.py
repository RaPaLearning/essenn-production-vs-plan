from __future__ import annotations

import os
import sys
import unittest
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd

# Allow import from parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import (
    build_date_index,
    extract_date_from_sheet,
    get_file_path,
    handle_user_selection,
    load_sheet_with_auto_header,
    main,
    show_jobs,
)


class TestOperationsPlanner(unittest.TestCase):
    # -------------------------------
    # DATE EXTRACTION
    # -------------------------------
    @patch("main.pd.read_excel")
    def test_extract_date_success(self, mock_read: MagicMock) -> None:
        data = [[""] * 6 for _ in range(6)]
        data[1][1] = "2026-04-06"
        mock_read.return_value = pd.DataFrame(data)

        result = extract_date_from_sheet("xl", "Sheet1")  # type: ignore[arg-type]
        self.assertEqual(result, "2026-04-06")

    @patch("main.pd.read_excel")
    def test_extract_date_none(self, mock_read: MagicMock) -> None:
        data = [[""] * 6 for _ in range(6)]
        mock_read.return_value = pd.DataFrame(data)

        result = extract_date_from_sheet("xl", "Sheet1")  # type: ignore[arg-type]
        self.assertIsNone(result)

    # -------------------------------
    # BUILD INDEX
    # -------------------------------
    @patch("main.pd.read_excel")
    @patch("main.pd.ExcelFile")
    def test_build_date_index_success(self, mock_excel: MagicMock, mock_read: MagicMock) -> None:
        mock_excel.return_value.sheet_names = ["Sheet1"]

        data = [[""] * 6 for _ in range(6)]
        data[2][2] = "2026-04-06"
        mock_read.return_value = pd.DataFrame(data)

        index = build_date_index("file.xlsx")
        self.assertIn("2026-04-06", index)

    @patch("main.pd.read_excel")
    @patch("main.pd.ExcelFile")
    def test_build_date_index_no_date(self, mock_excel: MagicMock, mock_read: MagicMock) -> None:
        mock_excel.return_value.sheet_names = ["Sheet1"]

        data = [[""] * 6 for _ in range(6)]
        mock_read.return_value = pd.DataFrame(data)

        index = build_date_index("file.xlsx")
        self.assertEqual(index, {})

    # -------------------------------
    # HEADER DETECTION
    # -------------------------------
    @patch("main.pd.read_excel")
    def test_header_detection(self, mock_read: MagicMock) -> None:
        raw = pd.DataFrame(
            [
                ["junk", ""],
                ["Job ID", "Product Name"],
                ["A", "B"],
            ]
        )

        processed = pd.DataFrame(columns=["job id", "product name"])
        mock_read.side_effect = [raw, processed]

        df = load_sheet_with_auto_header("file", "sheet")
        self.assertIn("job id", df.columns)

    @patch("main.pd.read_excel")
    def test_header_fallback(self, mock_read: MagicMock) -> None:
        # 🔥 Covers line 72
        raw = pd.DataFrame(
            [
                ["abc", "def"],
                ["ghi", "jkl"],
            ]
        )

        processed = pd.DataFrame(columns=["col1", "col2"])

        mock_read.side_effect = [raw, processed]

        df = load_sheet_with_auto_header("file", "sheet")
        self.assertIsNotNone(df)

    # -------------------------------
    # SHOW JOBS
    # -------------------------------
    @patch("main.load_sheet_with_auto_header")
    @patch("builtins.input", return_value="")
    def test_show_jobs_success(self, mock_input: MagicMock, mock_load: MagicMock) -> None:
        mock_load.return_value = pd.DataFrame({"job": ["A", "B"]})
        show_jobs("file", "sheet", "2026-04-06")

    @patch("main.load_sheet_with_auto_header")
    @patch("builtins.input", return_value="")
    def test_show_jobs_empty(self, mock_input: MagicMock, mock_load: MagicMock) -> None:
        mock_load.return_value = pd.DataFrame({"job": []})
        show_jobs("file", "sheet", "2026-04-06")

    @patch("main.load_sheet_with_auto_header")
    @patch("builtins.input", return_value="")
    def test_show_jobs_no_column(self, mock_input: MagicMock, mock_load: MagicMock) -> None:
        mock_load.return_value = pd.DataFrame({"x": [1]})
        show_jobs("file", "sheet", "2026-04-06")

    # -------------------------------
    # FILE PATH
    # -------------------------------
    @patch("main.glob.glob", return_value=["file.xlsx"])
    def test_get_file_path_success(self, mock_glob: MagicMock) -> None:
        self.assertEqual(get_file_path(), "file.xlsx")

    @patch("main.glob.glob", return_value=[])
    def test_get_file_path_fail(self, mock_glob: MagicMock) -> None:
        with self.assertRaises(FileNotFoundError):
            get_file_path()

    # -------------------------------
    # USER INPUT HANDLER
    # -------------------------------
    @patch("builtins.input", return_value="q")
    def test_handle_quit(self, mock_input: MagicMock) -> None:
        self.assertFalse(handle_user_selection("p", {}, []))

    @patch("builtins.input", side_effect=["abc", ""])
    def test_handle_invalid(self, mock_input: MagicMock) -> None:
        self.assertTrue(handle_user_selection("p", {"d": "s"}, ["d"]))

    @patch("main.show_jobs")
    @patch("builtins.input", return_value="0")
    def test_handle_valid(self, mock_input: MagicMock, mock_show: MagicMock) -> None:
        self.assertTrue(handle_user_selection("p", {"d": "s"}, ["d"]))

    # -------------------------------
    # MAIN FUNCTION
    # -------------------------------
    @patch("builtins.input", side_effect=["999", "q"])
    @patch("main.get_file_path", return_value="file.xlsx")
    @patch("main.build_date_index", return_value={"2026-04-06": "Sheet1"})
    def test_main_invalid_choice(
        self,
        mock_idx: MagicMock,
        mock_path: MagicMock,
        mock_input: MagicMock,
    ) -> None:
        main()

    @patch("builtins.input", return_value="q")
    @patch("main.get_file_path", return_value="file.xlsx")
    @patch("main.build_date_index", return_value={})
    def test_main_no_dates(
        self,
        mock_idx: MagicMock,
        mock_path: MagicMock,
        mock_input: MagicMock,
    ) -> None:
        main()

    # -------------------------------
    # DISPLAY DATES
    # -------------------------------
    def test_display_dates_line_wrap(self) -> None:
        """Covers the line-wrap branch (i+1) % 4 == 0."""
        from main import display_dates

        # 4 items → triggers the print() newline branch
        display_dates(["2026-04-01", "2026-04-02", "2026-04-03", "2026-04-04"])

    def test_display_dates_no_wrap(self) -> None:
        """Covers path where (i+1) % 4 != 0 for all items."""
        from main import display_dates

        display_dates(["2026-04-01", "2026-04-02"])

    # -------------------------------
    # PARSE DATE CELL
    # -------------------------------
    def test_parse_date_cell_valid(self) -> None:
        from main import parse_date_cell

        result = parse_date_cell("2026-04-06")
        self.assertIsNotNone(result)

    def test_parse_date_cell_dayfirst(self) -> None:
        from main import parse_date_cell

        result = parse_date_cell("06/04/2026")
        self.assertIsNotNone(result)

    def test_parse_date_cell_invalid(self) -> None:
        from main import parse_date_cell

        result = parse_date_cell("not-a-date")
        self.assertIsNone(result)

    # -------------------------------
    # CLEAR SCREEN
    # -------------------------------
    def test_clear_screen(self) -> None:
        from main import clear_screen

        clear_screen()  # just ensure it doesn't crash

    # -------------------------------
    # MAIN ERROR BRANCH
    # -------------------------------
    @patch("main.get_file_path", side_effect=FileNotFoundError("no file"))
    def test_main_exception(self, mock_path: MagicMock) -> None:
        """Covers the except branch in main()."""
        main()

    # -------------------------------
    # EXTRACT DATE FROM SHEET - edge coverage
    # -------------------------------
    @patch("main.pd.read_excel")
    def test_extract_date_dayfirst(self, mock_read: MagicMock) -> None:
        data: list[list[Any]] = [[""] * 6 for _ in range(6)]
        data[0][0] = "06/04/2026"
        mock_read.return_value = pd.DataFrame(data)

        result = extract_date_from_sheet("xl", "Sheet1")  # type: ignore[arg-type]
        self.assertIsNotNone(result)
