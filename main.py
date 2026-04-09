"""Entry point for essenn-production-vs-plan.

Usage:
    python main.py <YYYY-MM-DD>

Example:
    python main.py 2026-03-14

Reads data/sample/OperationsByDay.xlsx and writes the result to
output/jobs_<date>.txt
"""

import os
import sys
from datetime import date

from get_jobs_by_date import get_jobs_by_date

EXCEL_FILE = os.path.join(os.path.dirname(__file__), "data", "sample", "OperationsByDay.xlsx")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def _parse_date_arg() -> date:
    if len(sys.argv) != 2:
        print("Usage: python main.py <YYYY-MM-DD>")
        print("Example: python main.py 2026-03-14")
        sys.exit(1)
    try:
        return date.fromisoformat(sys.argv[1])
    except ValueError:
        print(f"Error: '{sys.argv[1]}' is not a valid date. Use YYYY-MM-DD format.")
        sys.exit(1)


def _write_output(jobs: list[str], target_date: date) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_file = os.path.join(OUTPUT_DIR, f"jobs_{target_date}.txt")
    with open(output_file, "w") as f:
        f.write(f"Jobs active on {target_date}\n")
        f.write(f"Total: {len(jobs)}\n")
        f.write("-" * 40 + "\n")
        for i, job in enumerate(jobs, 1):
            f.write(f"{i:3}. {job}\n")
    return output_file


def main() -> None:
    target_date = _parse_date_arg()
    print(f"Reading: {EXCEL_FILE}")
    print(f"Target date: {target_date}\n")
    jobs = get_jobs_by_date(EXCEL_FILE, target_date)
    print(f"Jobs active on {target_date} ({len(jobs)} found):")
    for job in jobs:
        print(f"  {job}")
    output_file = _write_output(jobs, target_date)
    print(f"\nOutput saved to: {output_file}")


if __name__ == "__main__":  # pragma: no cover
    main()
