import time
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

# Route-specific limit rules: (method, path_prefix) -> (max_requests, window_seconds)
ROUTE_LIMITS: Dict[Tuple[str, str], Tuple[int, int]] = {
    ("POST", "/api/v1/reports"): (10, 60),       # Email dispatch / generation: 10/min
    ("POST", "/api/v1/scans"): (20, 60),         # Scan initiation: 20/min
    ("POST", "/api/v1/domains"): (30, 60),       # Domain registration: 30/min
    ("POST", "/api/v1/billing/create-order"): (20, 60),  # Order creation: 20/min
    ("GET", "/telemetry"): (15, 60),             # Infrastructure reconnaissance telemetry: 15/min
}

DEFAULT_LIMIT = (120, 60)  # 120 req / 60s for general endpoints


class SlidingWindowRateLimiter:
    """
    In-memory thread-safe sliding window rate limiter.
    """

    def __init__(self):
        # Key: f"{route_key}:{client_ip}" -> list of request timestamps
        self._history: Dict[str, List[float]] = defaultdict(list)

    def is_rate_limited(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int]:
        """
        Returns (is_limited, remaining_quota, retry_after_seconds).
        """
        now = time.time()
        window_start = now - window_seconds
        timestamps = self._history[key]

        # Prune expired timestamps
        valid_timestamps = [t for t in timestamps if t > window_start]
        self._history[key] = valid_timestamps

        if len(valid_timestamps) >= max_requests:
            oldest = valid_timestamps[0]
            retry_after = max(1, int((oldest + window_seconds) - now))
            return True, 0, retry_after

        # Record this request
        valid_timestamps.append(now)
        remaining = max(0, max_requests - len(valid_timestamps))
        return False, remaining, 0

    def clear(self):
        self._history.clear()


limiter = SlidingWindowRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Protects API from automated scraping, flood attacks, and brute force abuse.
    """

    async def dispatch(self, request: Request, call_next):
        # Skip health check and CORS preflight requests
        if request.url.path in ("/health", "/api/v1/health") or request.method == "OPTIONS":
            return await call_next(request)

        # Resolve client IP (supporting reverse proxies like Caddy/Cloudflare)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        elif request.client:
            client_ip = request.client.host
        else:
            client_ip = "127.0.0.1"

        # Determine route-specific rate limit
        method = request.method
        path = request.url.path

        max_requests, window_seconds = DEFAULT_LIMIT
        matched_rule = "default"

        for (rule_method, rule_path), (rule_max, rule_win) in ROUTE_LIMITS.items():
            if method == rule_method and (path.startswith(rule_path) or rule_path in path):
                max_requests = rule_max
                window_seconds = rule_win
                matched_rule = f"{rule_method}:{rule_path}"
                break

        key = f"{matched_rule}:{client_ip}"
        is_limited, remaining, retry_after = limiter.is_rate_limited(
            key=key,
            max_requests=max_requests,
            window_seconds=window_seconds,
        )

        if is_limited:
            logger.warning(f"Rate limit exceeded for {client_ip} on {method} {path} (Retry-After: {retry_after}s)")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please wait before making more requests.",
                    "retry_after": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
