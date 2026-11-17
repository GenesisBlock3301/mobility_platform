"""Fixed-window rate limiter kept in this process's memory.

Limits: counters reset when the process restarts and are not shared between
processes, so the API runs as a single worker. With several workers this would
move to Redis.
"""

import math
import time
from dataclasses import dataclass, field
from threading import Lock

WINDOW_SECONDS = 60
# Hard cap on distinct clients tracked per window, so a flood of new client keys
# cannot grow memory without bound. New clients beyond the cap are refused until
# the window rolls over (fail closed).
MAX_KEYS = 20_000


@dataclass
class FixedWindowLimiter:
    window_seconds: int = WINDOW_SECONDS
    max_keys: int = MAX_KEYS
    _window: int = -1
    _counts: dict[tuple[str, str], int] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def hit(self, client: str, bucket: str, limit: int, now: float | None = None) -> tuple[bool, int]:
        """Count one request. Returns (allowed, seconds until the window resets)."""
        now = time.time() if now is None else now
        window = int(now // self.window_seconds)
        retry_after = max(1, math.ceil((window + 1) * self.window_seconds - now))
        key = (client, bucket)
        with self._lock:
            if window != self._window:
                # A new window: every old counter is obsolete. O(1), once per window.
                self._window = window
                self._counts = {}
            if key not in self._counts and len(self._counts) >= self.max_keys:
                return False, retry_after
            count = self._counts.get(key, 0) + 1
            self._counts[key] = count
        return count <= limit, retry_after
