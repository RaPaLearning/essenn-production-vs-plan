import pandas as pd
from datetime import datetime


def _parse_dates(start_raw, end_raw):
    try:
        start = pd.to_datetime(str(start_raw).strip(), dayfirst=True).date()
        end = pd.to_datetime(str(end_raw).strip(), dayfirst=True).date()
        return start, end
    except Exception:
        return None


def _process_row(row, target):
    order = row.iloc[0]
    start_raw = row.iloc[8]
    end_raw = row.iloc[10]

    if pd.isna(order) or pd.isna(start_raw) or pd.isna(end_raw):
        return None

    parsed = _parse_dates(start_raw, end_raw)
    if not parsed:
        return None

    start, end = parsed

    if start <= target <= end:
        return str(order).strip()

    return None


def _process_sheet(df, target):
    if df.shape[0] < 6:
        return []

    results = []

    for _, row in df.iloc[5:].iterrows():
        job = _process_row(row, target)
        if job:
            results.append(job)

    return results


def get_active_jobs(file_path: str, date_str: str) -> list[str]:
    target = datetime.strptime(date_str, "%Y-%m-%d").date()
    sheets = pd.read_excel(file_path, sheet_name=None, header=None)

    result = []
    for df in sheets.values():
        result.extend(_process_sheet(df, target))

    return result
