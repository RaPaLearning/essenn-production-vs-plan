import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from get_active_jobs import get_active_jobs

FIXTURE = "tests/fixtures/test_operations.xlsx"


def test_jobs_spanning_date():
    jobs = get_active_jobs(FIXTURE, "2026-03-10")

    assert "J2602-0028" in jobs
    assert "J2601-0054" in jobs
    assert "J2603-0072/97" in jobs


def test_job_not_spanning_date():
    jobs = get_active_jobs(FIXTURE, "2026-03-20")

    assert "J2602-0020" not in jobs


def test_empty_date_returns_nothing():
    jobs = get_active_jobs(FIXTURE, "2026-01-01")

    assert jobs == []
