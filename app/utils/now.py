from datetime import datetime, timezone
import os

def now_utc():
    fixed = os.getenv("NOW_UTC")
    if fixed:
        return datetime.fromisoformat(fixed.replace("Z","+00:00")).astimezone(timezone.utc)
    return datetime.now(timezone.utc)
