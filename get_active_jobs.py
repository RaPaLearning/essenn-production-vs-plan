import pandas as pd
from datetime import datetime


def get_active_jobs(file_path: str, date_str: str) -> list[str]:
    target = datetime.strptime(date_str, "%Y-%m-%d").date()
    sheets = pd.read_excel(file_path, sheet_name=None, header=None)
    result = []

    for df in sheets.values():
        if df.shape[0] < 6:
            continue
        for _, row in df.iloc[5:].iterrows():
            order = row.iloc[0]
            start_raw = row.iloc[8]
            end_raw = row.iloc[10]
            if pd.isna(order) or pd.isna(start_raw) or pd.isna(end_raw):
                continue
            try:
                start = pd.to_datetime(str(start_raw).strip(), dayfirst=True).date()
                end = pd.to_datetime(str(end_raw).strip(), dayfirst=True).date()
                if start <= target <= end:
                    result.append(str(order).strip())
            except Exception:
                continue

    return result