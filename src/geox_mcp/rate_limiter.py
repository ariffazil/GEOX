"""Simple per-connection rate limiter for GEOX tools."""
import time
from collections import defaultdict


class RateLimiter:
    def __init__(self):
        self._calls: dict[str, list[float]] = defaultdict(list)

    def check(self, session_id: str, tier: str) -> bool:
        now = time.time()
        window = 60.0  # 1 minute
        max_calls = 30 if tier == "anon" else 100 if tier == "session" else 999

        # Clean old entries
        self._calls[session_id] = [t for t in self._calls[session_id] if now - t < window]

        if len(self._calls[session_id]) >= max_calls:
            return False  # rate limited

        self._calls[session_id].append(now)
        return True


rate_limiter = RateLimiter()
