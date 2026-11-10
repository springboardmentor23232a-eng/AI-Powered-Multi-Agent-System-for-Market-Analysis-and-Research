import time
from collections import defaultdict, deque
from typing import Callable

from fastapi import HTTPException, Request

from app.core.config import settings


class SlidingWindowLimiter:
    """In-memory limiter. Per process, so run a single API worker (documented in docs/DEPLOYMENT.md)."""

    def __init__(self, window_seconds: float = 60.0, clock: Callable[[], float] = time.monotonic):
        self.window, self.clock = window_seconds, clock
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, limit: int) -> bool:
        now = self.clock()
        q = self.hits[key]
        while q and now - q[0] >= self.window:
            q.popleft()
        if len(q) >= limit:
            return False
        q.append(now)
        return True

    def reset(self) -> None:
        self.hits.clear()


auth_limiter = SlidingWindowLimiter()


def auth_rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    if not auth_limiter.allow(ip, settings.auth_attempts_per_minute):
        raise HTTPException(429, "Too many attempts. Try again in a minute.", headers={"Retry-After": "60"})
