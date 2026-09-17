from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return naive UTC datetime (compatible across SQLite and Postgres)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
