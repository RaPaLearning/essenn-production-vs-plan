"""Tests for main.py CLI entry point — ensures 100 % branch coverage."""

import os
import sys
import unittest
from io import StringIO
from unittest.mock import patch

# Allow running from tests/ or from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import main  # noqa: E402

_OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "output", "jobs_2026-03-14.txt")


def _run_happy_path() -> None:
    """Run main() with a valid date and return silently."""
    with patch.object(sys, "argv", ["main.py", "2026-03-14"]):
        with patch("sys.stdout", new_callable=StringIO):
            main.main()


class TestMainCLI(unittest.TestCase):
    # ------------------------------------------------------------------
    # Wrong number of arguments → exit(1)
    # ------------------------------------------------------------------

    def test_no_args_exits(self) -> None:
        with patch.object(sys, "argv", ["main.py"]):
            with self.assertRaises(SystemExit) as ctx:
                main.main()
        self.assertEqual(ctx.exception.code, 1)

    def test_too_many_args_exits(self) -> None:
        with patch.object(sys, "argv", ["main.py", "2026-03-14", "extra"]):
            with self.assertRaises(SystemExit) as ctx:
                main.main()
        self.assertEqual(ctx.exception.code, 1)

    # ------------------------------------------------------------------
    # Invalid date format → exit(1)
    # ------------------------------------------------------------------

    def test_invalid_date_exits(self) -> None:
        with patch.object(sys, "argv", ["main.py", "not-a-date"]):
            with self.assertRaises(SystemExit) as ctx:
                main.main()
        self.assertEqual(ctx.exception.code, 1)

    # ------------------------------------------------------------------
    # Happy path — valid date, real Excel file
    # ------------------------------------------------------------------

    def test_happy_path_creates_output_file(self) -> None:
        _run_happy_path()
        self.assertTrue(os.path.exists(_OUTPUT_FILE))

    def test_happy_path_output_file_content(self) -> None:
        _run_happy_path()
        with open(_OUTPUT_FILE) as f:
            content = f.read()
        self.assertIn("Jobs active on 2026-03-14", content)
        self.assertIn("Total: 32", content)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
