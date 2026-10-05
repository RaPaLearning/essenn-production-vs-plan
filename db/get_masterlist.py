"""Retrieve the Masterlist from Supabase."""

import pandas as pd
from db.client import supabase


def get_masterlist() -> pd.DataFrame:
    """Fetch all masterlist rows from Supabase and return as a DataFrame."""
    if supabase is None:  # type: ignore[reportUnnecessaryComparison]
        print("Supabase client is not initialized.")
        return pd.DataFrame()

    try:
        res = supabase.table("masterlist").select("*").execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        print(f"Error fetching masterlist: {e}")
        return pd.DataFrame()
