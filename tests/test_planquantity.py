import datetime
import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from planquantity import compute_plan_qty


class TestComputePlanQty(unittest.TestCase):
    def test_with_valid_times(self) -> None:
        """Compute plan qty using actual start/end datetimes."""
        start = datetime.datetime(2026, 3, 10, 6, 0)
        end = datetime.datetime(2026, 3, 10, 18, 0)  # 12 hours
        # speed = 120 / 12 = 10 per hour, plan = 10 * 8 = 80
        self.assertEqual(compute_plan_qty(120.0, start, end), 80)

    def test_with_none_dates_falls_back_to_24h(self) -> None:
        """When dates are None, default to 24-hour window."""
        # speed = 240 / 24 = 10 per hour, plan = 10 * 8 = 80
        self.assertEqual(compute_plan_qty(240.0, None, None), 80)

    def test_with_zero_qty_returns_one(self) -> None:
        """Plan qty should never be zero; minimum is 1."""
        self.assertEqual(compute_plan_qty(0.0, None, None), 1)

    def test_with_end_before_start_falls_back_to_24h(self) -> None:
        """When end <= start, default to 24-hour window."""
        start = datetime.datetime(2026, 3, 10, 18, 0)
        end = datetime.datetime(2026, 3, 10, 6, 0)  # end before start
        # speed = 240 / 24 = 10, plan = 80
        self.assertEqual(compute_plan_qty(240.0, start, end), 80)
