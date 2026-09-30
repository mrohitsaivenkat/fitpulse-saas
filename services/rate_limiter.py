"""
FitPulse SaaS - Rate Limiting & Throttling Service (Phase 3D)
Provides in-memory sliding-window request throttling for abuse mitigation:
- Mitigates brute-force credential stuffing and password guessing on /login.
- Mitigates registration spam on /register.
- Automatically purges expired timestamps to maintain minimal memory footprint.
"""
import time
from collections import defaultdict
from typing import Dict, List, Tuple
from functools import wraps

try:
    from flask import request, jsonify
    _HAS_FLASK = True
except ImportError:
    _HAS_FLASK = False
    request = None
    jsonify = None


class SlidingWindowRateLimiter:
    """In-memory sliding window rate limiter."""
    def __init__(self):
        # Maps key -> list of float timestamps
        self._records: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        """
        Check if request under `key` is allowed within `window_seconds`.
        Returns (is_allowed, retry_after_seconds).
        """
        now = time.time()
        cutoff = now - window_seconds

        # Filter out expired timestamps
        timestamps = [ts for ts in self._records[key] if ts > cutoff]
        self._records[key] = timestamps

        if len(timestamps) >= max_requests:
            oldest = timestamps[0]
            retry_after = max(1, int(oldest + window_seconds - now))
            return False, retry_after

        # Record this request
        self._records[key].append(now)
        return True, 0

    def reset(self, key: str):
        """Reset counter for a given key upon successful action."""
        if key in self._records:
            del self._records[key]


# Global rate limiter instance
limiter = SlidingWindowRateLimiter()


def rate_limit(max_requests: int = 10, window_seconds: int = 60, key_func=None):
    """
    Decorator for throttling sensitive routes.
    Defaults to 10 requests per 60 seconds per client IP.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not _HAS_FLASK or not request:
                return f(*args, **kwargs)

            # Determine client identifier
            if key_func:
                client_key = key_func()
            else:
                client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1")
                client_key = f"{request.endpoint}:{client_ip.split(',')[0].strip()}"

            allowed, retry_after = limiter.is_allowed(client_key, max_requests, window_seconds)
            if not allowed:
                response = jsonify({
                    "error": f"Too many attempts. Please try again in {retry_after} seconds.",
                    "status_code": 429,
                    "retry_after": retry_after
                })
                response.status_code = 429
                response.headers["Retry-After"] = str(retry_after)
                return response

            return f(*args, **kwargs)
        return decorated_function
    return decorator
