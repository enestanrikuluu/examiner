from __future__ import annotations

import time
import uuid
from typing import Any

from fastapi import HTTPException, Request
import redis.asyncio as aioredis

from src.core.config import settings


_redis_pool: Any = None


async def get_redis_pool() -> Any:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(settings.redis_url)
    return _redis_pool


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def __call__(self, request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{client_ip}:{request.url.path}"
        now = time.time()
        window_start = now - self.window_seconds

        redis_client = await get_redis_pool()
        async with redis_client.pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zadd(key, {f"{now}:{uuid.uuid4().hex[:8]}": now})
            pipe.zcard(key)
            pipe.expire(key, self.window_seconds + 1)
            results = await pipe.execute()

        request_count: int = results[2]
        if request_count > self.max_requests:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")


standard_rate_limit = RateLimiter(max_requests=60, window_seconds=60)
ai_rate_limit = RateLimiter(max_requests=10, window_seconds=60)
auth_rate_limit = RateLimiter(max_requests=20, window_seconds=60)
