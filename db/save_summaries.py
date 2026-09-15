"""Save generated operations summaries to Supabase."""

from db.client import supabase


def _parse_int(row: dict[str, str], key: str) -> int | None:
    """Parse an integer from a row dict, returning None if not a digit."""
    val = str(row.get(key, ""))
    return int(val) if val.isdigit() else None


def _build_row(date_str: str, r: dict[str, str]) -> dict[str, str | int | None]:
    """Build a single Supabase row dict from a summary row."""
    return {
        "date": date_str,
        "shift": r.get("Shift", ""),
        "machine": r.get("Machine", ""),
        "job_order_no": r.get("Job Order No", ""),
        "total_qty": _parse_int(r, "Total QTY"),
        "part_no": r.get("Part No", ""),
        "part_name": r.get("Part Name", ""),
        "operation": r.get("Operation", ""),
        "plan_qty": _parse_int(r, "Plan Qty"),
        "ok_qty": _parse_int(r, "OK QTY"),
    }


def save_report_summaries(
    date_str: str,
    rows: list[dict[str, str]],
    anomalies: list[dict[str, str]],
) -> None:
    """Save the generated summary rows to Supabase."""
    if supabase is None:  # type: ignore[reportUnnecessaryComparison]
        return

    all_data = [_build_row(date_str, r) for r in rows]

    if all_data:
        try:
            supabase.table("summaries").insert(all_data).execute()
        except Exception as e:
            print(f"Error saving summaries: {e}")
