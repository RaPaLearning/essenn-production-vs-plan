"""Compute planned quantity per 8-hour shift using setup and cycle time."""

import datetime
from typing import Iterator

SHIFT_HOURS: float = 8.0


def get_shifts_in_range(
    start_dt: datetime.datetime, end_dt: datetime.datetime
) -> Iterator[tuple[str, datetime.date, datetime.datetime, datetime.datetime]]:
    """Yield all shifts spanning from start_dt to end_dt."""
    current_date = start_dt.date() - datetime.timedelta(days=1)
    end_date = end_dt.date() + datetime.timedelta(days=1)

    while current_date <= end_date:
        s1_start = datetime.datetime.combine(current_date, datetime.time(6, 0))
        s1_end = datetime.datetime.combine(current_date, datetime.time(14, 0))

        s2_start = datetime.datetime.combine(current_date, datetime.time(14, 0))
        s2_end = datetime.datetime.combine(current_date, datetime.time(22, 0))

        s3_start = datetime.datetime.combine(current_date, datetime.time(22, 0))
        s3_end = datetime.datetime.combine(
            current_date + datetime.timedelta(days=1), datetime.time(6, 0)
        )

        yield ("Shift I", current_date, s1_start, s1_end)
        yield ("Shift II", current_date, s2_start, s2_end)
        yield ("Shift III", current_date, s3_start, s3_end)

        current_date += datetime.timedelta(days=1)


def compute_shift_plan_quantities(
    qty: float,
    start_dt: datetime.datetime,
    end_dt: datetime.datetime,
    target_date: datetime.date,
    setup_minutes: float = 0.0,
    cycle_minutes_per_item: float = 0.0,
) -> dict[str, int]:  # noqa: C901
    """Compute planned quantity for each shift on the target date.

    Simulates production from start_dt to end_dt.
    Deducts setup time only on the first shift with overlap.
    Caps cumulative production at qty.
    """
    result = {"Shift I": 0, "Shift II": 0, "Shift III": 0}

    if end_dt <= start_dt:
        end_dt = start_dt + datetime.timedelta(days=1)

    total_qty = int(qty)
    cumulative_qty = 0
    setup_applied = False

    total_duration_hours = (end_dt - start_dt).total_seconds() / 3600.0
    speed = total_qty / total_duration_hours if total_duration_hours > 0 else 0

    for shift_name, shift_date, shift_start, shift_end in get_shifts_in_range(start_dt, end_dt):
        overlap_start = max(start_dt, shift_start)
        overlap_end = min(end_dt, shift_end)

        overlap_mins = (overlap_end - overlap_start).total_seconds() / 60.0

        if overlap_mins <= 0:
            continue

        if cycle_minutes_per_item > 0.0:
            if not setup_applied:
                avail_mins = overlap_mins - setup_minutes
                setup_applied = True
            else:
                avail_mins = overlap_mins

            if avail_mins > 0:
                produced = int(avail_mins / cycle_minutes_per_item)
            else:
                produced = 0
        else:
            produced = int(round(speed * (overlap_mins / 60.0)))

        remaining = total_qty - cumulative_qty

        if remaining <= 0:
            produced = 0
        else:
            if produced <= 0 and overlap_mins > 0:
                produced = 1
            produced = min(produced, remaining)

        cumulative_qty += produced

        if shift_date == target_date:
            result[shift_name] = produced

    return result
