"""Parse setup and cycle times from the Opcenter masterlist XLS file."""

import re
from typing import TypeAlias

import pandas as pd

# Lookup key: (Part No, Operation Name) -> (setup_minutes, cycle_minutes_per_item)
CycleTimeLookup: TypeAlias = dict[tuple[str, str], tuple[float, float]]

_TIME_RE = re.compile(
    r"(\d+)\s*Hours?\s+(\d+(?:\.\d+)?)\s*Mins?",
    re.IGNORECASE,
)


def _parse_time_string(raw: object) -> float:
    """Convert a string like '1 Hours 02.5000 Mins' to total minutes.

    Returns 0.0 for unparseable or missing values.
    """
    if pd.isna(raw):  # type: ignore[arg-type]
        return 0.0
    text = str(raw).strip()
    m = _TIME_RE.search(text)
    if m is None:
        return 0.0
    hours = float(m.group(1))
    mins = float(m.group(2))
    return hours * 60.0 + mins


def load_cycle_times(xls_path: str) -> CycleTimeLookup:
    """Load the Opcenter masterlist and return a lookup dict.

    The XLS has columns:
        0: Part No.  (forward-fill needed for merged cells)
        1: Product
        2: Op. No.
        3: Operation Name
        4: Setup Time
        5: Op. Time per Item

    Row 0 is the header row; data starts at row 1.

    Returns a dict mapping (part_no, operation_name) -> (setup_minutes, cycle_minutes).
    """
    df: pd.DataFrame = pd.read_excel(  # type: ignore[reportUnknownMemberType]
        xls_path, header=None
    )

    # Drop the header row (row 0)
    df = df.iloc[1:].reset_index(drop=True)

    # Forward-fill Part No (column 0) for merged cells
    df.iloc[:, 0] = df.iloc[:, 0].ffill()  # type: ignore[reportUnknownMemberType]

    lookup: CycleTimeLookup = {}

    for _, row in df.iterrows():
        part_no_raw: object = row.iloc[0]
        op_name_raw: object = row.iloc[3]

        if pd.isna(part_no_raw) or pd.isna(op_name_raw):  # type: ignore[arg-type]
            continue

        part_no = str(part_no_raw).strip()
        op_name = str(op_name_raw).strip()

        setup_mins = _parse_time_string(row.iloc[4])
        cycle_mins = _parse_time_string(row.iloc[5])

        lookup[(part_no, op_name)] = (setup_mins, cycle_mins)

    return lookup


def get_cycle_minutes(
    lookup: CycleTimeLookup,
    part_no: str,
    operation_name: str,
) -> tuple[float, float]:
    """Look up setup and cycle time for a (part_no, operation_name) pair.

    Returns (setup_minutes, cycle_minutes_per_item).
    Returns (0.0, 0.0) if not found.
    """
    return lookup.get((part_no.strip(), operation_name.strip()), (0.0, 0.0))
