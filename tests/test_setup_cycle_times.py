import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from setup_cycle_times import (
    CycleTimeLookup,
    _parse_time_string,  # type: ignore[reportPrivateUsage]
    get_cycle_minutes,
    load_cycle_times,
)


class TestParseTimeString(unittest.TestCase):
    def test_simple_minutes(self) -> None:
        self.assertAlmostEqual(_parse_time_string("0 Hours 03 Mins"), 3.0)

    def test_hours_and_minutes(self) -> None:
        self.assertAlmostEqual(_parse_time_string("1 Hours 02.5000 Mins"), 62.5)

    def test_zero_time(self) -> None:
        self.assertAlmostEqual(_parse_time_string("0 Hours 00 Mins"), 0.0)

    def test_large_time(self) -> None:
        self.assertAlmostEqual(_parse_time_string("2 Hours 30 Mins"), 150.0)

    def test_nan_returns_zero(self) -> None:
        self.assertAlmostEqual(_parse_time_string(float("nan")), 0.0)

    def test_none_returns_zero(self) -> None:
        self.assertAlmostEqual(_parse_time_string(None), 0.0)

    def test_garbage_returns_zero(self) -> None:
        self.assertAlmostEqual(_parse_time_string("not a time"), 0.0)


class TestLoadCycleTimes(unittest.TestCase):
    def _create_test_xls(self) -> str:
        """Create a temporary XLSX file with test data matching the expected format."""
        data = [
            # Header row (row 0)
            ["Part No.", "Product", "Op. No.", "Operation Name", "Setup Time", "Op. Time per Item"],
            # Part 1, Op 1
            ["PART-001", "Widget A", 10, "Turning 1st", "0 Hours 20 Mins", "0 Hours 01 Mins"],
            # Part 1, Op 2 (blank Part No — forward fill)
            [None, None, 20, "Turning 2nd", "0 Hours 30 Mins", "0 Hours 02 Mins"],
            # Part 2
            ["PART-002", "Widget B", 10, "Milling 1st", "1 Hours 00 Mins", "0 Hours 05 Mins"],
        ]
        df = pd.DataFrame(data)
        tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        tmp.close()
        df.to_excel(tmp.name, index=False, header=False)  # type: ignore[reportUnknownMemberType]
        return tmp.name

    def test_load_basic(self) -> None:
        path = self._create_test_xls()
        try:
            lookup = load_cycle_times(path)
            # Should have 3 entries
            self.assertEqual(len(lookup), 3)
            # Check PART-001, Turning 1st
            self.assertEqual(lookup[("PART-001", "Turning 1st")], (20.0, 1.0))
            # Check forward-filled PART-001, Turning 2nd
            self.assertEqual(lookup[("PART-001", "Turning 2nd")], (30.0, 2.0))
            # Check PART-002, Milling 1st
            self.assertEqual(lookup[("PART-002", "Milling 1st")], (60.0, 5.0))
        finally:
            os.remove(path)

    def test_load_real_masterlist(self) -> None:
        """Test loading the actual bundled masterlist file."""
        real_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "data",
            "sample",
            "Opcenter masterlist of components.xls",
        )
        if not os.path.exists(real_path):
            self.skipTest("Real masterlist not available")

        lookup = load_cycle_times(real_path)
        self.assertGreater(len(lookup), 0)

        # Spot-check a known entry from the file
        # 2D555550R, Turning 1st -> setup=20min, cycle=1min
        result = get_cycle_minutes(lookup, "2D555550R", "Turning 1st")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertAlmostEqual(result[0], 20.0)
        self.assertAlmostEqual(result[1], 1.0)

    @patch("os.path.exists")
    def test_load_real_masterlist_skipped(self, mock_exists: MagicMock) -> None:
        """Cover the skipTest branch inside test_load_real_masterlist."""
        mock_exists.return_value = False
        with self.assertRaises(unittest.SkipTest):
            self.test_load_real_masterlist()




class TestGetCycleMinutes(unittest.TestCase):
    def test_found(self) -> None:
        lookup: CycleTimeLookup = {("P1", "Op1"): (10.0, 2.0)}
        self.assertEqual(get_cycle_minutes(lookup, "P1", "Op1"), (10.0, 2.0))

    def test_not_found_returns_none(self) -> None:
        lookup: CycleTimeLookup = {}
        self.assertIsNone(get_cycle_minutes(lookup, "P1", "Op1"))

    def test_whitespace_stripping(self) -> None:
        lookup: CycleTimeLookup = {("P1", "Op1"): (5.0, 1.5)}
        self.assertEqual(get_cycle_minutes(lookup, " P1 ", " Op1 "), (5.0, 1.5))
