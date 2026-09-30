"""Run SQL migration files against Supabase."""

import os
from pathlib import Path

import httpx
from db.client import supabase


def _apply_migration(url: str, key: str, sql: str) -> None:
    """Send a single migration SQL to Supabase via HTTP."""
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    resp = httpx.post(
        f"{url}/rest/v1/rpc/",
        headers=headers,
        json={"query": sql},
        timeout=30,
    )
    if resp.status_code != 200:
        httpx.post(
            f"{url}/rest/v1/",
            headers={**headers, "Prefer": "return=representation"},
            json={"query": sql},
            timeout=30,
        )


def run_migrations() -> None:
    """Read and execute all .sql files in migrations/ in sorted order."""
    if not supabase:
        print("Supabase client not initialized")
        return

    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        print("SUPABASE_URL and SUPABASE_KEY must be set")
        return

    migrations_dir = Path("migrations")
    for file in sorted(migrations_dir.glob("*.sql")):
        sql = file.read_text(encoding="utf-8")
        print(f"Running {file.name}...")
        _apply_migration(url, key, sql)
        print(f"Applied {file.name}")


if __name__ == "__main__":
    run_migrations()
