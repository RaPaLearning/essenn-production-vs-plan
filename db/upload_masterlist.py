"""Upload the Masterlist Excel file to Supabase."""

import pandas as pd
from db.client import supabase


def _build_row(row: pd.Series) -> dict[str, str | float | None]:  # type: ignore[reportUnknownParameterType]
    """Build a single Supabase row dict from a masterlist DataFrame row."""
    ct_sec = pd.to_numeric(row.get("CT \nSEC"), errors="coerce")  # type: ignore[reportCallIssue, reportUnknownVariableType]
    ct_val: float | None = None if pd.isna(ct_sec) else float(ct_sec)  # type: ignore[reportUnknownArgumentType]
    return {
        "part_no": str(row.get("PART NO.", "")).strip(),
        "part_name": str(row.get("PART NAME", "")).strip(),
        "operation_no": str(row.get("OPN NO.", "")).strip(),
        "operation_name": str(row.get("OPERATION NAME", "")).strip(),
        "resource": str(row.get("RESOURCE", "")).strip(),
        "ct_sec": ct_val,
        "machine_type": str(row.get("MACHINE TYPE", "")).strip(),
    }


def upload_masterlist(file_path: str) -> int:
    """Reads the masterlist Excel file and uploads it to Supabase."""
    if supabase is None:  # type: ignore[reportUnnecessaryComparison]
        print("Supabase client is not initialized.")
        return 0

    print(f"Reading {file_path}...")
    df: pd.DataFrame = pd.read_excel(file_path)  # type: ignore[reportUnknownMemberType]

    # Columns: PART NO., PART NAME, OPN NO., OPERATION NAME,
    #          RESOURCE, CT \nSEC, MACHINE TYPE
    all_data: list[dict[str, str | float | None]] = [
        _build_row(row) for _, row in df.iterrows()  # type: ignore[reportUnknownArgumentType]
    ]

    print(f"Uploading {len(all_data)} rows to Supabase...")

    try:
        res = supabase.table("masterlist").insert(all_data).execute()
        print("Upload complete!")
        return len(res.data)
    except Exception as e:
        print(f"Error uploading masterlist: {e}")
        return 0


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        upload_masterlist(sys.argv[1])
    else:
        print("Please provide the path to the masterlist excel file.")
