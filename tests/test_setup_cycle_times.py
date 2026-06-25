import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from setup_cycle_times import (
    CycleTimeLookup,
    MachineTypeLookup,
    _normalize_machine_name,  # type: ignore[reportPrivateUsage]
    _parse_time_string,  # type: ignore[reportPrivateUsage]
    get_cycle_minutes,
    get_machine_type,
    load_cycle_times,
    load_machine_types,
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
        assert result is not None  # nosec B101
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


class TestNormalizeMachineName(unittest.TestCase):
    def test_lowercase(self) -> None:
        self.assertEqual(_normalize_machine_name("ACE COLT"), "ace colt")

    def test_hyphen_to_space(self) -> None:
        self.assertEqual(_normalize_machine_name("CITIZEN-1"), "citizen 1")

    def test_collapse_whitespace(self) -> None:
        self.assertEqual(_normalize_machine_name("LMW  ST  2"), "lmw st 2")

    def test_combined_normalization(self) -> None:
        self.assertEqual(_normalize_machine_name("  DX100 - 2  "), "dx100 2")


class TestGetMachineType(unittest.TestCase):
    def test_exact_match_turning(self) -> None:
        lookup: MachineTypeLookup = {"doosan 1": "turning"}
        self.assertEqual(get_machine_type(lookup, "Doosan 1"), "turning")

    def test_exact_match_milling(self) -> None:
        lookup: MachineTypeLookup = {"doosan vmc 1": "milling"}
        self.assertEqual(get_machine_type(lookup, "Doosan VMC 1"), "milling")

    def test_fuzzy_match_citizen(self) -> None:
        """'Citizen 1' should match 'CITIZEN-1' via normalization."""
        lookup: MachineTypeLookup = {"citizen 1": "milling"}
        self.assertEqual(get_machine_type(lookup, "Citizen 1"), "milling")

    def test_prefix_match_jyoti_vmc(self) -> None:
        """'Jyoti VMC 1' should match 'Jyoti VMC 1 - PX20' via prefix."""
        lookup: MachineTypeLookup = {"jyoti vmc 1 px20": "milling"}
        self.assertEqual(get_machine_type(lookup, "Jyoti VMC 1"), "milling")

    def test_unknown_defaults_to_turning(self) -> None:
        lookup: MachineTypeLookup = {"doosan 1": "turning"}
        self.assertEqual(get_machine_type(lookup, "Unknown Machine XYZ"), "turning")

    def test_empty_lookup_defaults_to_turning(self) -> None:
        lookup: MachineTypeLookup = {}
        self.assertEqual(get_machine_type(lookup, "Any Machine"), "turning")


class TestLoadMachineTypes(unittest.TestCase):
    def test_load_real_machine_list(self) -> None:
        """Test loading the actual machine list from the new masterlist."""
        real_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "data",
            "sample",
            "Mater list of Component(Preactor)-1 (1) (1).xls",
        )
        if not os.path.exists(real_path):
            self.skipTest("New masterlist not available")

        lookup = load_machine_types(real_path)
        self.assertGreater(len(lookup), 0)

        # Spot-check known machines
        self.assertEqual(get_machine_type(lookup, "Doosan VMC 1"), "milling")
        self.assertEqual(get_machine_type(lookup, "Citizen 1"), "milling")
        self.assertEqual(get_machine_type(lookup, "Doosan 1"), "turning")
        self.assertEqual(get_machine_type(lookup, "Jyoti 2"), "turning")

    @patch("os.path.exists")
    def test_load_real_machine_list_skipped(self, mock_exists: MagicMock) -> None:
        """Cover the skipTest branch inside test_load_real_machine_list."""
        mock_exists.return_value = False
        with self.assertRaises(unittest.SkipTest):
            self.test_load_real_machine_list()

    def test_load_machine_types_with_nan_rows(self) -> None:
        """Cover the NaN-skip branch in load_machine_types."""
        # Build a minimal "Machine list" sheet matching the real layout:
        # Rows 0-5 are header/blank, data starts at row 6.
        blank: list[object] = [None, None, None, None, None]
        header: list[object] = [None, "SL No", "Machine", "Main Group", "Sub group"]
        data_rows: list[list[object]] = [
            blank, blank, blank, blank,
            header,
            blank,  # row 5: blank separator
            [None, 1, "TestTurning", "Turning", "2axis"],
            [None, None, None, None, None],  # NaN row to cover the continue
            [None, 2, "TestMilling", "Milling", "4 axis"],
        ]
        df = pd.DataFrame(data_rows)
        tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        tmp.close()
        with pd.ExcelWriter(tmp.name) as writer:  # type: ignore[reportUnknownVariableType]
            df.to_excel(writer, sheet_name="Machine list", index=False, header=False)  # type: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        try:
            lookup = load_machine_types(tmp.name)
            self.assertEqual(len(lookup), 2)
            self.assertEqual(get_machine_type(lookup, "TestTurning"), "turning")
            self.assertEqual(get_machine_type(lookup, "TestMilling"), "milling")
        finally:
            os.remove(tmp.name)
