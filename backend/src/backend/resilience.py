"""
Task D6: Resilience utilities — rate limiting and error handling.
"""

import time
from fastapi import HTTPException

from backend.log import log


class RateLimiter:
    """In-memory sliding window rate limiter per emp_id."""

    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.history: dict[str, list[float]] = {}

    def check_rate_limit(self, emp_id: str) -> None:
        """Raises HTTPException 429 if emp_id has exceeded rate limit."""
        now = time.time()
        timestamps = self.history.get(emp_id, [])

        # Filter out timestamps outside the active sliding window
        valid = [t for t in timestamps if now - t < self.window_seconds]

        if len(valid) >= self.max_requests:
            log(f"⛔ RATE LIMIT EXCEEDED for {emp_id} ({len(valid)} reqs in {self.window_seconds}s)")
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: maximum {self.max_requests} requests per {self.window_seconds}s. Please wait.",
            )

        valid.append(now)
        self.history[emp_id] = valid
