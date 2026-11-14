"""Simple in-memory login rate limiter.

Limits login attempts per (IP, identifier) pair. Suitable for a single-instance
development deployment; replace with Redis for multi-instance production.
"""

import time
from collections import defaultdict, deque

MAX_ATTEMPTS = 5
WINDOW_SECONDS = 300  # 5 minutes

_attempts: dict[str, deque[float]] = defaultdict(deque)


def is_rate_limited(key: str) -> bool:
    now = time.time()
    q = _attempts[key]
    while q and now - q[0] > WINDOW_SECONDS:
        q.popleft()
    return len(q) >= MAX_ATTEMPTS


def record_attempt(key: str) -> None:
    _attempts[key].append(time.time())


def reset_attempts(key: str) -> None:
    _attempts.pop(key, None)
