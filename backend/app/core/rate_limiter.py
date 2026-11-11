import time
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import HTTPException, status


class InMemoryRateLimiter:
    """
    Simple, secure sliding-window rate limiter for brute-force prevention on authentication routes.
    Can be replaced with Redis in distributed deployments.
    """
    def __init__(self, max_attempts: int = 5, window_seconds: int = 300, lockout_seconds: int = 300):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self.failed_attempts: Dict[str, List[float]] = defaultdict(list)
        self.locked_until: Dict[str, float] = {}

    def _cleanup(self, key: str, now: float) -> None:
        self.failed_attempts[key] = [t for t in self.failed_attempts[key] if now - t < self.window_seconds]

    def check_rate_limit(self, key: str) -> None:
        now = time.time()
        
        # Check if locked out
        if key in self.locked_until:
            if now < self.locked_until[key]:
                remaining = int(self.locked_until[key] - now)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many failed login attempts. Please wait {remaining} seconds before trying again."
                )
            else:
                del self.locked_until[key]
                self.failed_attempts[key] = []

        self._cleanup(key, now)
        if len(self.failed_attempts[key]) >= self.max_attempts:
            self.locked_until[key] = now + self.lockout_seconds
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed attempts. Account temporarily locked for {self.lockout_seconds // 60} minutes."
            )

    def record_failure(self, key: str) -> None:
        now = time.time()
        self.failed_attempts[key].append(now)
        if len(self.failed_attempts[key]) >= self.max_attempts:
            self.locked_until[key] = now + self.lockout_seconds

    def reset(self, key: str) -> None:
        if key in self.failed_attempts:
            del self.failed_attempts[key]
        if key in self.locked_until:
            del self.locked_until[key]


login_rate_limiter = InMemoryRateLimiter(max_attempts=5, window_seconds=300, lockout_seconds=300)

