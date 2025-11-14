"""
Rate Limiting Middleware

요청 횟수 제한 (DoS 공격 방지)
"""

from fastapi import HTTPException, Request
from typing import Dict, Tuple
import time
from collections import defaultdict
import os

# Rate limit 설정
RATE_LIMIT_ENABLED = os.getenv("ENABLE_RATE_LIMIT", "false").lower() == "true"
REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))
REQUESTS_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "500"))
REQUESTS_PER_DAY = int(os.getenv("RATE_LIMIT_PER_DAY", "3000"))


class RateLimiter:
    """
    Simple in-memory rate limiter

    Tracks request counts per client IP for different time windows
    """

    def __init__(self):
        # {client_ip: [(timestamp, count)]}
        self.requests: Dict[str, list] = defaultdict(list)

    def _clean_old_requests(self, client_ip: str, window_seconds: int):
        """Remove requests older than window"""
        now = time.time()
        cutoff = now - window_seconds
        self.requests[client_ip] = [
            (ts, count) for ts, count in self.requests[client_ip]
            if ts > cutoff
        ]

    def _count_requests(self, client_ip: str, window_seconds: int) -> int:
        """Count requests within window"""
        self._clean_old_requests(client_ip, window_seconds)
        return sum(count for _, count in self.requests[client_ip])

    def check_rate_limit(self, client_ip: str) -> Tuple[bool, str]:
        """
        Check if client has exceeded rate limit

        Args:
            client_ip: Client IP address

        Returns:
            (is_allowed, limit_type) where limit_type is the exceeded limit
        """
        if not RATE_LIMIT_ENABLED:
            return True, ""

        # Check minute limit
        minute_count = self._count_requests(client_ip, 60)
        if minute_count >= REQUESTS_PER_MINUTE:
            return False, f"per-minute ({REQUESTS_PER_MINUTE})"

        # Check hour limit
        hour_count = self._count_requests(client_ip, 3600)
        if hour_count >= REQUESTS_PER_HOUR:
            return False, f"per-hour ({REQUESTS_PER_HOUR})"

        # Check day limit
        day_count = self._count_requests(client_ip, 86400)
        if day_count >= REQUESTS_PER_DAY:
            return False, f"per-day ({REQUESTS_PER_DAY})"

        return True, ""

    def record_request(self, client_ip: str):
        """Record a request from client"""
        if not RATE_LIMIT_ENABLED:
            return

        now = time.time()
        self.requests[client_ip].append((now, 1))


# Global rate limiter instance
rate_limiter = RateLimiter()


async def check_rate_limit(request: Request):
    """
    FastAPI dependency to check rate limit

    Usage:
        @app.get("/api/endpoint", dependencies=[Depends(check_rate_limit)])
        async def endpoint():
            return {"message": "OK"}
    """
    client_ip = request.client.host if request.client else "unknown"

    is_allowed, limit_type = rate_limiter.check_rate_limit(client_ip)

    if not is_allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {limit_type}. Please try again later."
        )

    rate_limiter.record_request(client_ip)
