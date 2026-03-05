from typing import Any

from redis.asyncio import Redis

from src.core.config import settings

redis_client: Any = Redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


async def get_redis() -> Any:
    return redis_client
