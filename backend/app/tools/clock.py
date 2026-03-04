from datetime import datetime, timezone


def current_utc() -> str:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    return f"Current UTC time: {now.isoformat()}"
