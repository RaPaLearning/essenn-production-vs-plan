import datetime
import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from planquantity import compute_shift_plan_quantities


class TestComputeShiftPlanQuantities(unittest.TestCase):
    def test_setup_deducted_only_first_shift(self) -> None:
        """Setup time should only be deducted in the first shift with overlap."""
        # 10 hours total: 10:00 to 20:00 on the same day
        # Shift A: 10:00 to 14:00 (4 hours = 240 mins)
        # Shift B: 14:00 to 20:00 (6 hours = 360 mins)
        start = datetime.datetime(2026, 3, 10, 10, 0)
        end = datetime.datetime(2026, 3, 10, 20, 0)
        target = datetime.date(2026, 3, 10)

        # Setup = 60 mins, Cycle = 2 mins
        # Shift A: avail = 240 - 60 = 180 mins -> 90 items
        # Shift B: avail = 360 mins -> 180 items
        # Total items = 270. Let's make qty 500 so it doesn't cap.
        result, anomalies = compute_shift_plan_quantities(
            qty=500.0,
            start_dt=start,
            end_dt=end,
            target_date=target,
            setup_minutes=60.0,
            cycle_minutes_per_item=2.0,
        )

        self.assertEqual(result["Shift A"], 90)
        self.assertEqual(result["Shift B"], 180)
        self.assertEqual(result["Shift C"], 0)
        self.assertEqual(anomalies, [])

    def test_capped_at_total_qty(self) -> None:
        """Production should be capped when cumulative sum reaches total qty."""
        # Shift A: 08:00 to 14:00 (360 mins)
        # Setup = 0, Cycle = 1 min
        # Shift A capacity = 360 items.
        # But total qty is only 150 items.
        start = datetime.datetime(2026, 3, 10, 8, 0)
        end = datetime.datetime(2026, 3, 10, 20, 0)
        target = datetime.date(2026, 3, 10)

        result, anomalies = compute_shift_plan_quantities(
            qty=150.0,
            start_dt=start,
            end_dt=end,
            target_date=target,
            setup_minutes=0.0,
            cycle_minutes_per_item=1.0,
        )

        self.assertEqual(result["Shift A"], 150)
        self.assertEqual(result["Shift B"], 0)
        self.assertEqual(result["Shift C"], 0)
        self.assertEqual(anomalies, [])

    def test_legacy_fallback(self) -> None:
        """When cycle time is 0, use proportional speed allocation."""
        # 10 hours total. Qty = 100. Speed = 10 items/hour.
        # Shift A: 10:00 to 14:00 (4 hours) -> 40 items
        # Shift B: 14:00 to 20:00 (6 hours) -> 60 items
        start = datetime.datetime(2026, 3, 10, 10, 0)
        end = datetime.datetime(2026, 3, 10, 20, 0)
        target = datetime.date(2026, 3, 10)

        result, anomalies = compute_shift_plan_quantities(
            qty=100.0,
            start_dt=start,
            end_dt=end,
            target_date=target,
            setup_minutes=0.0,
            cycle_minutes_per_item=0.0,
        )

        self.assertEqual(result["Shift A"], 40)
        self.assertEqual(result["Shift B"], 60)
        self.assertEqual(result["Shift C"], 0)
        self.assertEqual(anomalies, [])

    def test_anomaly_when_setup_exceeds_available(self) -> None:
        """When setup time exceeds shift duration, report anomaly with 0 qty."""
        # Shift A: 10:00 to 11:00 (60 mins)
        # Setup = 120 mins. Avail = 60 - 120 = -60 mins. Math yields 0.
        # Should report anomaly instead of silently defaulting to 1.
        start = datetime.datetime(2026, 3, 10, 10, 0)
        end = datetime.datetime(2026, 3, 10, 11, 0)
        target = datetime.date(2026, 3, 10)

        result, anomalies = compute_shift_plan_quantities(
            qty=10.0,
            start_dt=start,
            end_dt=end,
            target_date=target,
            setup_minutes=120.0,
            cycle_minutes_per_item=2.0,
        )

        self.assertEqual(result["Shift A"], 0)
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["shift"], "Shift A")
        self.assertIn("Setup time", anomalies[0]["reason"])

    def test_invalid_date_range_fallback(self) -> None:
        """When end <= start, fallback to a 24-hour interval."""
        start = datetime.datetime(2026, 3, 10, 20, 0)
        end = datetime.datetime(2026, 3, 10, 10, 0)  # Invalid
        target = datetime.date(2026, 3, 10)

        # Will fallback to start + 1 day = 2026-03-11 20:00 (24 hours)
        # On target date 2026-03-10:
        # Shift B: 2 hours -> 20 items.
        # Shift C: 8 hours -> 80 items.
        result, _ = compute_shift_plan_quantities(
            qty=240.0,
            start_dt=start,
            end_dt=end,
            target_date=target,
            setup_minutes=0.0,
            cycle_minutes_per_item=0.0,
        )

        self.assertEqual(result["Shift A"], 0)
        self.assertEqual(result["Shift B"], 20)
        self.assertEqual(result["Shift C"], 80)
