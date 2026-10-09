"""Supabase client initialization."""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url: str = os.environ.get("SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_KEY", "")

# We allow empty strings during CI environments without secrets
if url and key:
    supabase: Client = create_client(url, key)
else:
    # Fallback to a mock/none type in tests without env vars
    supabase = None  # type: ignore[assignment]
