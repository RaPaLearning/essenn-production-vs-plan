import datetime
from typing import Any
import pandas as pd
from planquantity import compute_plan_qty


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


def _process_row(row: "pd.Series[Any]", target: datetime.date) -> dict[str, Any] | None:
    """Return order details if the row's job is active on target date."""
    order: object = row.iloc[0]
    if pd.isna(order):  # type: ignore[arg-type]
        return None

    start: datetime.date | None = _parse_date(row, 8)
    end: datetime.date | None = _parse_date(row, 10)

    if start is None or end is None:
        return None

    if start <= target <= end:
        machine: object = row.iloc[7]
        machine_str: str = str(machine).strip() if not pd.isna(machine) else ""  # type: ignore[arg-type]

        # Extract template fields
        product: object = row.iloc[1]
        part_no: object = row.iloc[2]
        qty: object = row.iloc[3]
        op_name: object = row.iloc[6]

        qty_val = float(qty) if not pd.isna(qty) else 0.0  # type: ignore[arg-type]
        part_no_str = str(part_no).strip() if not pd.isna(part_no) else ""  # type: ignore[arg-type]
        product_str = str(product).strip() if not pd.isna(product) else ""  # type: ignore[arg-type]
        op_name_str = str(op_name).strip() if not pd.isna(op_name) else ""  # type: ignore[arg-type]

        start_dt = _parse_datetime(row, 8)
        end_dt = _parse_datetime(row, 10)
        plan_qty = compute_plan_qty(qty_val, start_dt, end_dt)

        return {
            "Machine": machine_str,
            "Job Order No": str(order).strip(),
            "Total Qty": int(qty_val),
            "Part No": part_no_str,
            "Part Name": product_str,
            "Operation": op_name_str,
            "Plan Qty": plan_qty,
        }

    return None


def _process_sheet(df: pd.DataFrame, target: datetime.date) -> list[dict[str, Any]]:
    """Return all active job records from a single sheet."""
    if df.shape[0] < 6:
        return []

    results: list[dict[str, Any]] = []
    for _, row in df.iloc[5:].iterrows():
        record = _process_row(row, target)
        if record:
            results.append(record)
    return results


def get_active_jobs(input_path: str, date_str: str) -> list[dict[str, Any]]:
    """Load the Excel file and return all active job records for the given date."""
    target: datetime.date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    sheets: dict[str, pd.DataFrame] = pd.read_excel(  # type: ignore[reportUnknownMemberType]
        input_path, sheet_name=None, header=None
    )
    rows: list[dict[str, Any]] = []
    for df in sheets.values():
        rows.extend(_process_sheet(df, target))
    return rows
