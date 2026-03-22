"""
Simple in-memory sliding-window rate limiter for FastAPI.
No external dependencies — uses only the standard library.
"""

import time
import logging
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)


class SlidingWindowRateLimiter:
    """Thread-safe sliding-window rate limiter keyed by arbitrary string."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, deque] = defaultdict(deque)
        self._lock = Lock()

    def is_allowed(self, key: str) -> bool:
        """Return True if the request should be allowed, False if throttled."""
        now = time.monotonic()
        cutoff = now - self.window_seconds

        with self._lock:
            bucket = self._buckets[key]
            # Evict timestamps outside the window
            while bucket and bucket[0] < cutoff:
                bucket.popleft()

            if len(bucket) >= self.max_requests:
                return False

            bucket.append(now)
            return True

    def reset(self, key: str) -> None:
        """Clear all recorded requests for a key (useful in tests)."""
        with self._lock:
            self._buckets.pop(key, None)


# 5 login attempts per 60 s per IP
login_rate_limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=60)

# 3 registrations per 5 min per IP
register_rate_limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=300)


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_login_rate_limit(request: Request) -> None:
    """FastAPI dependency — enforce login rate limit."""
    ip = _get_client_ip(request)
    if not login_rate_limiter.is_allowed(ip):
        logger.warning("Login rate limit exceeded for IP: %s", ip)
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Please wait before trying again.",
            headers={"Retry-After": "60"},
        )


def check_register_rate_limit(request: Request) -> None:
    """FastAPI dependency — enforce registration rate limit."""
    ip = _get_client_ip(request)
    if not register_rate_limiter.is_allowed(ip):
        logger.warning("Registration rate limit exceeded for IP: %s", ip)
        raise HTTPException(
            status_code=429,
            detail="Too many registration attempts. Please wait before trying again.",
            headers={"Retry-After": "300"},
        )
