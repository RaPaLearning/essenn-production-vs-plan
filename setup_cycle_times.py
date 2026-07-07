"""Parse setup and cycle times from the Opcenter masterlist XLS file."""

import re
from typing import Literal, TypeAlias

import pandas as pd

MachineType: TypeAlias = Literal["turning", "milling"]

# Normalized machine name -> MachineType
MachineTypeLookup: TypeAlias = dict[str, MachineType]

_TWO_SHIFT_GROUPS = frozenset({"milling", "sliding head"})

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
) -> tuple[float, float] | None:
    """Look up setup and cycle time for a (part_no, operation_name) pair.

    Returns (setup_minutes, cycle_minutes_per_item).
    Returns None if not found in the master list.
    """
    return lookup.get((part_no.strip(), operation_name.strip()))


def _normalize_machine_name(name: str) -> str:
    """Normalize a machine name for fuzzy matching.

    Lowercases, strips hyphens, collapses whitespace.
    """
    text = name.lower().replace("-", " ")
    return " ".join(text.split())


def load_machine_types(xls_path: str) -> MachineTypeLookup:
    """Load the 'Machine list' sheet and return a normalized-name -> type lookup.

    The sheet layout (0-indexed columns):
        1: SL No
        2: Machine
        3: Main Group
        4: Sub group

    Rows 0-5 are header/blank; data starts at row 6.
    Machines whose Main Group is in _TWO_SHIFT_GROUPS are classified
    as ``"milling"``; everything else is ``"turning"``.
    """
    df: pd.DataFrame = pd.read_excel(  # type: ignore[reportUnknownMemberType]
        xls_path, sheet_name="Machine list", header=None
    )
    df = df.iloc[6:].reset_index(drop=True)

    lookup: MachineTypeLookup = {}
    for _, row in df.iterrows():
        name_raw: object = row.iloc[2]
        group_raw: object = row.iloc[3]
        if pd.isna(name_raw) or pd.isna(group_raw):  # type: ignore[arg-type]
            continue
        norm = _normalize_machine_name(str(name_raw))
        group = str(group_raw).strip().lower()
        machine_type: MachineType = "milling" if group in _TWO_SHIFT_GROUPS else "turning"
        lookup[norm] = machine_type

    return lookup


def _find_prefix_match(lookup: MachineTypeLookup, norm: str) -> str:
    """Find the best prefix match for a normalized machine name.

    Returns the matching key, or empty string if none found.
    """
    best_key = ""
    for key in lookup:
        if (norm.startswith(key) or key.startswith(norm)) and len(key) > len(best_key):
            best_key = key
    return best_key


def get_machine_type(
    lookup: MachineTypeLookup,
    machine: str,
) -> MachineType:
    """Look up the machine type using normalized name matching.

    Tries exact normalized match first, then prefix matching
    (longest matching prefix wins).  Falls back to ``"turning"``.
    """
    norm = _normalize_machine_name(machine)

    if norm in lookup:
        return lookup[norm]

    best = _find_prefix_match(lookup, norm)
    if best:
        return lookup[best]

    return "turning"
