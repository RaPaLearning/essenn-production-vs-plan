import datetime


def compute_plan_qty(
    qty: float,
    start_dt: datetime.datetime | None,
    end_dt: datetime.datetime | None,
) -> int:
    """Compute planned quantity per 8-hour shift based on timing."""
    if start_dt is not None and end_dt is not None and end_dt > start_dt:
        hours: float = (end_dt - start_dt).total_seconds() / 3600.0
    else:
        hours = 24.0

    speed: float = qty / hours if hours > 0 else 0
    plan_qty: int = int(round(speed * 8.0))

    if plan_qty <= 0:
        plan_qty = 1
    return plan_qty
