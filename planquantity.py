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

        yield ("Shift A", current_date, s1_start, s1_end)
        yield ("Shift B", current_date, s2_start, s2_end)
        yield ("Shift C", current_date, s3_start, s3_end)

        current_date += datetime.timedelta(days=1)


def _compute_overlap_minutes(
    start_dt: datetime.datetime,
    end_dt: datetime.datetime,
    shift_start: datetime.datetime,
    shift_end: datetime.datetime,
) -> float:
    """Compute the overlap in minutes between job and shift intervals."""
    overlap_start = max(start_dt, shift_start)
    overlap_end = min(end_dt, shift_end)
    return max((overlap_end - overlap_start).total_seconds() / 60.0, 0.0)


def _produce_with_cycle_time(
    overlap_mins: float,
    setup_minutes: float,
    cycle_minutes_per_item: float,
    setup_applied: bool,
) -> tuple[int, bool, str | None]:
    """Compute items produced in one shift using cycle time.

    Deducts setup on the first shift only.
    Returns (produced, setup_applied_after, anomaly_reason).
    """
    if not setup_applied:
        avail_mins = overlap_mins - setup_minutes
        setup_applied = True
    else:
        avail_mins = overlap_mins

    if avail_mins <= 0:
        reason = f"Setup time {setup_minutes} mins exceeds available {overlap_mins} mins"
        return 0, setup_applied, reason

    return int(avail_mins / cycle_minutes_per_item), setup_applied, None


def _produce_by_speed(overlap_mins: float, speed: float) -> int:
    """Compute items produced proportionally when cycle time is unknown."""
    return int(round(speed * (overlap_mins / 60.0)))


def _cap_production(produced: int, cumulative_qty: int, total_qty: int) -> int:
    """Cap produced so cumulative total does not exceed total_qty."""
    remaining = total_qty - cumulative_qty
    if remaining <= 0:
        return 0
    return min(produced, remaining)


def _compute_shift_production(
    overlap_mins: float,
    cycle_minutes_per_item: float,
    setup_minutes: float,
    speed: float,
    setup_applied: bool,
) -> tuple[int, bool, str | None]:
    """Compute production for one shift using either cycle time or speed."""
    if cycle_minutes_per_item > 0.0:
        return _produce_with_cycle_time(
            overlap_mins, setup_minutes, cycle_minutes_per_item, setup_applied
        )
    return _produce_by_speed(overlap_mins, speed), setup_applied, None


def _record_target_shift(
    shift_name: str,
    shift_date: datetime.date,
    target_date: datetime.date,
    produced: int,
    anomaly_reason: str | None,
    result: dict[str, int],
    anomalies: list[dict[str, str]],
) -> None:
    """Record production and anomalies for shifts on the target date."""
    if shift_date != target_date:
        return
    result[shift_name] = produced
    if anomaly_reason:
        anomalies.append({"shift": shift_name, "reason": anomaly_reason})


def _simulate_production(
    start_dt: datetime.datetime,
    end_dt: datetime.datetime,
    target_date: datetime.date,
    total_qty: int,
    cycle_minutes_per_item: float,
    setup_minutes: float,
    speed: float,
) -> tuple[dict[str, int], list[dict[str, str]]]:
    """Simulate shift-by-shift production and collect anomalies."""
    result: dict[str, int] = {"Shift A": 0, "Shift B": 0, "Shift C": 0}
    anomalies: list[dict[str, str]] = []
    cumulative_qty = 0
    setup_applied = False

    for shift_name, shift_date, shift_start, shift_end in get_shifts_in_range(start_dt, end_dt):
        overlap_mins = _compute_overlap_minutes(start_dt, end_dt, shift_start, shift_end)
        if overlap_mins <= 0:
            continue

        produced, setup_applied, anomaly_reason = _compute_shift_production(
            overlap_mins, cycle_minutes_per_item, setup_minutes, speed, setup_applied
        )
        produced = _cap_production(produced, cumulative_qty, total_qty)
        cumulative_qty += produced

        _record_target_shift(
            shift_name, shift_date, target_date, produced, anomaly_reason, result, anomalies
        )

    return result, anomalies


def compute_shift_plan_quantities(
    qty: float,
    start_dt: datetime.datetime,
    end_dt: datetime.datetime,
    target_date: datetime.date,
    setup_minutes: float = 0.0,
    cycle_minutes_per_item: float = 0.0,
) -> tuple[dict[str, int], list[dict[str, str]]]:
    """Compute planned quantity for each shift on the target date.

    Simulates production from start_dt to end_dt.
    Deducts setup time only on the first shift with overlap.
    Caps cumulative production at qty.

    Returns (shift_quantities, anomalies).
    """
    if end_dt <= start_dt:
        end_dt = start_dt + datetime.timedelta(days=1)

    total_qty = int(qty)
    total_duration_hours = (end_dt - start_dt).total_seconds() / 3600.0
    speed = total_qty / total_duration_hours if total_duration_hours > 0 else 0

    return _simulate_production(
        start_dt, end_dt, target_date, total_qty,
        cycle_minutes_per_item, setup_minutes, speed,
    )
