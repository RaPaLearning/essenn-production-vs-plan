<<<<<<< HEAD
import pandas as pd
import glob
import os
=======
from __future__ import annotations

import glob
import os
from typing import Any, cast

import pandas as pd
>>>>>>> e229566 (improvements:pyright_strict_mode)

# Terminal Colors
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
END = "\033[0m"


def clear_screen() -> None:
    print("\033c", end="")


<<<<<<< HEAD
def extract_date_from_sheet(xl, sheet):
    df = pd.read_excel(xl, sheet_name=sheet, header=None, nrows=6)
=======
def extract_date_from_sheet(xl: pd.ExcelFile, sheet: str) -> str | None:
    df: pd.DataFrame = cast(
        pd.DataFrame,
        pd.read_excel(xl, sheet_name=sheet, header=None, nrows=6),  # type: ignore[call-overload]
    )
>>>>>>> e229566 (improvements:pyright_strict_mode)

    for i in range(min(6, df.shape[0])):
        for j in range(min(6, df.shape[1])):
            val = parse_date_cell(df.iloc[i, j])

            if pd.notnull(val):
                return val.date().isoformat()

    return None


<<<<<<< HEAD
def get_file_path():
=======
def get_file_path() -> str:
>>>>>>> e229566 (improvements:pyright_strict_mode)
    """Find Excel file automatically."""
    for p in [os.path.join("data", "sample", "*.xlsx"), "data/sample/*.xlsx", "*.xlsx"]:
        files = glob.glob(p)
        if files:
            return files[0]
    raise FileNotFoundError("OperationsByDay.xlsx not found.")


# ✅ AUTO DATE DETECTION
<<<<<<< HEAD
def build_date_index(file_path):
    xl = pd.ExcelFile(file_path)
    date_to_sheet = {}

    print(f"{YELLOW}Indexing {len(xl.sheet_names)} operational days...{END}")

    for sheet in xl.sheet_names:
=======
def build_date_index(file_path: str) -> dict[str, str]:
    xl = pd.ExcelFile(file_path)
    date_to_sheet: dict[str, str] = {}

    print(f"{YELLOW}Indexing {len(xl.sheet_names)} operational days...{END}")

    for sheet_name_raw in xl.sheet_names:
        sheet = str(sheet_name_raw)
>>>>>>> e229566 (improvements:pyright_strict_mode)
        date = extract_date_from_sheet(xl, sheet)

        if date:
            date_to_sheet[date] = sheet
        else:
            print(f"{RED}No date found in sheet: {sheet}{END}")

    return dict(sorted(date_to_sheet.items()))


# ✅ SAFE HEADER DETECTION (FIXED FLOAT BUG)
<<<<<<< HEAD
def load_sheet_with_auto_header(file_path, sheet_name):
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

    header_row = None

    for i in range(min(10, len(df))):
        row = df.iloc[i].fillna("").astype(str).str.lower()
=======
def load_sheet_with_auto_header(file_path: str, sheet_name: str | int) -> pd.DataFrame:
    df: pd.DataFrame = cast(
        pd.DataFrame,
        pd.read_excel(file_path, sheet_name=sheet_name, header=None),  # type: ignore[call-overload]
    )

    header_row: int | None = None

    for i in range(min(10, len(df))):
        row: pd.Series[str] = df.iloc[i].fillna("").astype(str).str.lower()
>>>>>>> e229566 (improvements:pyright_strict_mode)

        if any("product" in cell or "job" in cell for cell in row):
            header_row = i
            break

    if header_row is None:
        header_row = 0  # fallback

<<<<<<< HEAD
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)
    df.columns = [str(c).strip().lower() for c in df.columns]

    return df


# ✅ SHOW JOBS
def show_jobs(file_path, sheet_name, date_label):
    df = load_sheet_with_auto_header(file_path, sheet_name)

    job_cols = [c for c in df.columns if "job" in c or "product" in c]
=======
    result: pd.DataFrame = cast(
        pd.DataFrame,
        pd.read_excel(file_path, sheet_name=sheet_name, header=header_row),  # type: ignore[call-overload]
    )
    result.columns = pd.Index([str(c).strip().lower() for c in result.columns])

    return result


# ✅ SHOW JOBS
def show_jobs(file_path: str, sheet_name: str | int, date_label: str) -> None:
    df = load_sheet_with_auto_header(file_path, sheet_name)

    job_cols: list[str] = [c for c in df.columns if "job" in str(c) or "product" in str(c)]
>>>>>>> e229566 (improvements:pyright_strict_mode)

    clear_screen()
    print(f"{BLUE}{BOLD}OPERATIONS REPORT: {date_label}{END}")
    print(f"{YELLOW}Excel Sheet: {sheet_name}{END}")
    print("─" * 45)

    if job_cols:
<<<<<<< HEAD
        jobs = sorted(df[job_cols[0]].dropna().astype(str).unique().tolist())
=======
        jobs: list[str] = sorted(df[job_cols[0]].dropna().astype(str).unique().tolist())
>>>>>>> e229566 (improvements:pyright_strict_mode)

        if jobs:
            for i, job in enumerate(jobs, 1):
                print(f" {BLUE}{i:2}.{END} {job}")
        else:
            print(f"{RED}No jobs found for this date.{END}")
    else:
        print(f"{RED}No 'Job/Product' column found.{END}")

    print("─" * 45)
    input(f"\n{GREEN}Press Enter to go back...{END}")


<<<<<<< HEAD
def display_dates(dates):
=======
def display_dates(dates: list[str]) -> None:
>>>>>>> e229566 (improvements:pyright_strict_mode)
    for i, d in enumerate(dates):
        print(f"{GREEN}[{i:2}]{END} {d}", end="\t")
        if (i + 1) % 4 == 0:
            print()


<<<<<<< HEAD
def handle_user_selection(path, date_map, available_dates):
=======
def handle_user_selection(path: str, date_map: dict[str, str], available_dates: list[str]) -> bool:
>>>>>>> e229566 (improvements:pyright_strict_mode)
    cmd = input(">> ").lower()

    if cmd == "q":
        return False

    if cmd.isdigit():
        idx = int(cmd)
        if 0 <= idx < len(available_dates):
            sel_date = available_dates[idx]
            show_jobs(path, date_map[sel_date], sel_date)
            return True

    input(f"{RED}Invalid choice. Press Enter...{END}")
    return True


<<<<<<< HEAD
def parse_date_cell(cell):
    val = pd.to_datetime(cell, errors="coerce")

    if pd.isna(val):
        val = pd.to_datetime(cell, errors="coerce", dayfirst=True)
=======
def parse_date_cell(cell: Any) -> pd.Timestamp | None:
    val = cast(pd.Timestamp | None, pd.to_datetime(cell, errors="coerce"))

    if val is None or pd.isna(val):
        val = cast(pd.Timestamp | None, pd.to_datetime(cell, errors="coerce", dayfirst=True))

    if val is None or pd.isna(val):
        return None
>>>>>>> e229566 (improvements:pyright_strict_mode)

    return val


# ✅ MAIN UI
<<<<<<< HEAD
def main():
=======
def main() -> None:
>>>>>>> e229566 (improvements:pyright_strict_mode)
    try:
        path = get_file_path()
        date_map = build_date_index(path)
        available_dates = list(date_map.keys())

        if not available_dates:
            print(f"{RED}No dates found in file!{END}")
            return

        running = True
        while running:
            clear_screen()
            print(f"{BLUE}{BOLD}=== SELECT OPERATIONAL DATE ==={END}\n")

            display_dates(available_dates)

            print(f"\n\n{BOLD}Choose (0-{len(available_dates) - 1}) or 'q' to quit:{END}")

            running = handle_user_selection(path, date_map, available_dates)

    except Exception as e:
        print(f"\n{RED}Error: {e}{END}")


if __name__ == "__main__":
    main()
