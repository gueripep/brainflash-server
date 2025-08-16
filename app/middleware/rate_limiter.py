"""
Simple in-memory rate limiter middleware for FastAPI/Starlette.

This implements a per-key (by default client IP) fixed window counter
using cachetools.TTLCache. It's suitable for single-process deployments
and development. For production/distributed deployments use Redis-backed
limiters.
"""
from typing import Callable, List, Optional
import threading

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from cachetools import TTLCache


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware.

    Parameters
    - max_requests: maximum requests allowed in the window
    - window_seconds: window size in seconds
    - key_func: function(Request) -> str to identify client (defaults to IP)
    - exempt_paths: list of request.path strings to skip rate limiting
    """

    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60,
                 key_func: Optional[Callable[[Request], str]] = None,
                 exempt_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.max_requests = int(max_requests)
        self.window = int(window_seconds)
        # The cache stores integer counters and automatically expires keys
        # after `window_seconds`.
        self.cache = TTLCache(maxsize=10000, ttl=self.window)
        self.lock = threading.Lock()
        self.key_func = key_func or self._default_key
        self.exempt_paths = exempt_paths or []

    def _default_key(self, request: Request) -> str:
        client = request.client.host if request.client else "unknown"
        return client

    async def dispatch(self, request: Request, call_next):
        # Don't rate limit exempt paths
        path = request.url.path
        if path in self.exempt_paths:
            return await call_next(request)

        key = self.key_func(request)

        # Thread-safe increment
        with self.lock:
            count = self.cache.get(key, 0) + 1
            self.cache[key] = count

        if count > self.max_requests:
            # Fixed-window behaviour: clients should wait up to window seconds
            headers = {"Retry-After": str(self.window)}
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429, headers=headers)

        response = await call_next(request)
        return response
