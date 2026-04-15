import datetime
from typing import Any

import pandas as pd


def _parse_start_date(row: "pd.Series[Any]") -> datetime.date | None:
    """Parse the start date from column index 8."""
    raw: object = row.iloc[8]
    if pd.isna(raw):  # type: ignore[arg-type]
        return None
    try:
        return pd.to_datetime(str(raw).strip(), dayfirst=True).date()  # type: ignore[union-attr]
    except Exception:
        return None


def _parse_end_date(row: "pd.Series[Any]") -> datetime.date | None:
    """Parse the end date from column index 10."""
    raw: object = row.iloc[10]
    if pd.isna(raw):  # type: ignore[arg-type]
        return None
    try:
        return pd.to_datetime(str(raw).strip(), dayfirst=True).date()  # type: ignore[union-attr]
    except Exception:
        return None


def _process_row(row: "pd.Series[Any]", target: datetime.date) -> str | None:
    order: object = row.iloc[0]

    if pd.isna(order):  # type: ignore[arg-type]
        return None

    start: datetime.date | None = _parse_start_date(row)
    end: datetime.date | None = _parse_end_date(row)

    if start is None or end is None:
        return None

    if start <= target <= end:
        return str(order).strip()

    return None


def _process_sheet(df: pd.DataFrame, target: datetime.date) -> list[str]:
    if df.shape[0] < 6:
        return []

    results: list[str] = []

    for _, row in df.iloc[5:].iterrows():
        job: str | None = _process_row(row, target)  # type: ignore[arg-type]
        if job:
            results.append(job)

    return results


def get_active_jobs(file_path: str, date_str: str) -> list[str]:
    target: datetime.date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    sheets: dict[str, pd.DataFrame] = pd.read_excel(  # type: ignore[reportUnknownMemberType]
        file_path, sheet_name=None, header=None
    )

    result: list[str] = []
    for df in sheets.values():
        result.extend(_process_sheet(df, target))

    return result
