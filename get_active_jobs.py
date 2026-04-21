import datetime
from typing import Any  # noqa: F401
import pandas as pd


def _parse_date(row: "pd.Series[Any]", index: int) -> datetime.date | None:
    """Parse a date from the given column index of a row."""
    raw: object = row.iloc[index]
    if pd.isna(raw):  # type: ignore[arg-type]
        return None
    try:
        return pd.to_datetime(str(raw).strip(), dayfirst=True).date()  # type: ignore[union-attr]
    except Exception:
        return None


def _process_row(row: "pd.Series[Any]", target: datetime.date) -> dict[str, str] | None:
    """Return order and machine if the row's job is active on target date."""
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
        return {"Order No.": str(order).strip(), "Machine": machine_str}

    return None


def _process_sheet(df: pd.DataFrame, target: datetime.date) -> list[dict[str, str]]:
    """Return all active job records from a single sheet."""
    if df.shape[0] < 6:
        return []

    results: list[dict[str, str]] = []
    for _, row in df.iloc[5:].iterrows():
        record: dict[str, str] | None = _process_row(row, target)  # type: ignore[arg-type]
        if record:
            results.append(record)
    return results


def export_active_jobs(input_path: str, date_str: str, output_path: str) -> None:
    """Export active jobs with machine names for a given date to an Excel file."""
    target: datetime.date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    sheets: dict[str, pd.DataFrame] = pd.read_excel(  # type: ignore[reportUnknownMemberType]
        input_path, sheet_name=None, header=None
    )

    rows: list[dict[str, str]] = []
    for df in sheets.values():
        rows.extend(_process_sheet(df, target))

    result: pd.DataFrame = pd.DataFrame(rows, columns=["Order No.", "Machine"])
    result.to_excel(output_path, index=False)  # type: ignore[reportUnknownMemberType]
