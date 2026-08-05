import datetime
from typing import Any, NamedTuple

import pandas as pd

from planquantity import SHIFTS_BY_TYPE, compute_shift_plan_quantities
from setup_cycle_times import (
    CycleTimeLookup,
    MachineType,
    MachineTypeLookup,
    get_cycle_minutes,
    get_machine_type,
)


class _ValidJob(NamedTuple):
    """A validated job extracted from a sheet row."""

    fields: dict[str, Any]
    start: datetime.date
    end: datetime.date
    machine_type: MachineType


def _safe_str(val: object) -> str:
    """Convert a cell value to a stripped string, returning '' for NaN."""
    if pd.isna(val):  # type: ignore[arg-type]
        return ""
    return str(val).strip()


def _parse_date(row: "pd.Series[Any]", index: int) -> datetime.date | None:
    """Parse a date from the given column index of a row."""
    raw: object = row.iloc[index]
    if pd.isna(raw):  # type: ignore[arg-type]
        return None
    try:
        return pd.to_datetime(str(raw).strip(), dayfirst=True).date()  # type: ignore[union-attr]
    except Exception:
        return None


def _parse_datetime(row: "pd.Series[Any]", index: int) -> datetime.datetime | None:
    """Parse a full datetime from the given column index of a row."""
    raw: object = row.iloc[index]
    if pd.isna(raw):  # type: ignore[arg-type]
        return None
    try:
        return pd.to_datetime(str(raw).strip(), dayfirst=True)
    except Exception:
        return None


def _extract_fields(row: "pd.Series[Any]") -> dict[str, Any]:
    """Extract and parse all relevant fields from a validated row."""
    qty_raw: object = row.iloc[3]
    return {
        "order": _safe_str(row.iloc[0]),
        "product": _safe_str(row.iloc[1]),
        "part_no": _safe_str(row.iloc[2]),
        "qty": float(qty_raw) if not pd.isna(qty_raw) else 0.0,  # type: ignore[arg-type]
        "op_name": _safe_str(row.iloc[6]),
        "machine": _safe_str(row.iloc[7]),
        "start_dt": _parse_datetime(row, 8),
        "end_dt": _parse_datetime(row, 10),
    }


def _resolve_cycle_time(
    cycle_lookup: CycleTimeLookup | None,
    part_no: str,
    op_name: str,
) -> tuple[float, float] | None:
    """Resolve setup and cycle time. Returns None if part not in master list."""
    if cycle_lookup is None:
        return (0.0, 0.0)
    return get_cycle_minutes(cycle_lookup, part_no, op_name)


def _base_record(fields: dict[str, Any]) -> dict[str, Any]:
    """Return the base dictionary common to all records and anomalies."""
    return {
        "Machine": fields["machine"],
        "Job Order No": fields["order"],
        "Total Qty": int(fields["qty"]),
        "Part No": fields["part_no"],
        "Part Name": fields["product"],
        "Operation": fields["op_name"],
    }


def _shift_names_for_type(machine_type: MachineType) -> list[str]:
    """Return shift names for the given machine type."""
    return [name for name, _, _ in SHIFTS_BY_TYPE[machine_type]]


def _make_lookup_anomalies(
    fields: dict[str, Any],
    machine_type: MachineType,
) -> list[dict[str, Any]]:
    """Create anomaly records for all shifts when part is not in master list."""
    reason = f"Part '{fields['part_no']}' / Op '{fields['op_name']}' not found in master list"
    return [
        {**_base_record(fields), "Shift": shift, "Anomaly": reason}
        for shift in _shift_names_for_type(machine_type)
    ]


def _build_shift_records(
    fields: dict[str, Any], shift_plans: dict[str, int]
) -> list[dict[str, Any]]:
    """Build output records for shifts with positive plan quantities."""
    return [
        {**_base_record(fields), "Plan Qty": plan_qty, "Shift": shift_name}
        for shift_name, plan_qty in shift_plans.items()
        if plan_qty > 0
    ]


def _build_shift_anomalies(
    fields: dict[str, Any], shift_anomalies: list[dict[str, str]]
) -> list[dict[str, Any]]:
    """Convert shift-level anomaly info into full anomaly records."""
    return [
        {**_base_record(fields), "Shift": a["shift"], "Anomaly": a["reason"]}
        for a in shift_anomalies
    ]


def _compute_and_build(
    fields: dict[str, Any],
    target: datetime.date,
    cycle_result: tuple[float, float],
    machine_type: MachineType,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Compute shift plans and build output records and anomalies."""
    setup_mins, cycle_mins = cycle_result
    shift_plans, shift_anomalies = compute_shift_plan_quantities(
        fields["qty"],
        fields["start_dt"],
        fields["end_dt"],
        target,
        setup_minutes=setup_mins,
        cycle_minutes_per_item=cycle_mins,
        machine_type=machine_type,
    )
    records = _build_shift_records(fields, shift_plans)
    anomalies = _build_shift_anomalies(fields, shift_anomalies)
    return records, anomalies


def _collect_valid_jobs(
    df: pd.DataFrame,
    machine_type_lookup: MachineTypeLookup | None,
) -> list[_ValidJob]:
    """Extract all valid jobs from a sheet's data rows."""
    valid_jobs: list[_ValidJob] = []
    for _, row in df.iloc[5:].iterrows():
        if pd.isna(row.iloc[0]):  # type: ignore[arg-type]
            continue
        start = _parse_date(row, 8)
        end = _parse_date(row, 10)
        if start is None or end is None:
            continue

        fields = _extract_fields(row)
        m_type: MachineType = (
            get_machine_type(machine_type_lookup, fields["machine"])
            if machine_type_lookup is not None
            else "turning"
        )
        valid_jobs.append(_ValidJob(fields, start, end, m_type))
    return valid_jobs


def _process_valid_job(
    fields: dict[str, Any],
    start: datetime.date,
    end: datetime.date,
    m_type: MachineType,
    target: datetime.date,
    same_as_prev: bool,
    cycle_lookup: CycleTimeLookup | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Process a single valid job, returning records and anomalies."""
    if not (start <= target <= end):
        return [], []

    cycle_result = _resolve_cycle_time(cycle_lookup, fields["part_no"], fields["op_name"])
    if cycle_result is None:
        return [], _make_lookup_anomalies(fields, m_type)

    setup_mins, cycle_mins = cycle_result
    if same_as_prev:
        setup_mins = 0.0

    return _compute_and_build(fields, target, (setup_mins, cycle_mins), m_type)


def _process_sheet(
    df: pd.DataFrame,
    target: datetime.date,
    cycle_lookup: CycleTimeLookup | None = None,
    machine_type_lookup: MachineTypeLookup | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return all active job records and anomalies from a single sheet."""
    if df.shape[0] < 6:
        return [], []

    valid_jobs = _collect_valid_jobs(df, machine_type_lookup)
    valid_jobs.sort(
        key=lambda job: (job.fields["machine"], job.fields["start_dt"] or datetime.datetime.min),
    )

    all_records: list[dict[str, Any]] = []
    all_anomalies: list[dict[str, Any]] = []
    prev_machine = None
    prev_part_no = None

    for job in valid_jobs:
        same_as_prev = (job.fields["machine"] == prev_machine) and (
            job.fields["part_no"] == prev_part_no
        )
        prev_machine = job.fields["machine"]
        prev_part_no = job.fields["part_no"]

        records, anomalies = _process_valid_job(
            job.fields,
            job.start,
            job.end,
            job.machine_type,
            target,
            same_as_prev,
            cycle_lookup,
        )
        all_records.extend(records)
        all_anomalies.extend(anomalies)

    return all_records, all_anomalies


def get_active_jobs(
    input_path: str,
    date_str: str,
    cycle_lookup: CycleTimeLookup | None = None,
    machine_type_lookup: MachineTypeLookup | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Load the Excel file and return all active job records and anomalies."""
    target: datetime.date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    sheets: dict[str, pd.DataFrame] = pd.read_excel(  # type: ignore[reportUnknownMemberType]
        input_path, sheet_name=None, header=None
    )
    rows: list[dict[str, Any]] = []
    anomalies: list[dict[str, Any]] = []
    for df in sheets.values():
        sheet_rows, sheet_anomalies = _process_sheet(
            df,
            target,
            cycle_lookup,
            machine_type_lookup,
        )
        rows.extend(sheet_rows)
        anomalies.extend(sheet_anomalies)
    return rows, anomalies
