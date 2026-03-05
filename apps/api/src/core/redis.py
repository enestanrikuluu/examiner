from redis.asyncio import Redis

from src.core.config import settings

redis_client = Redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


async def get_redis() -> Redis:  # type: ignore[type-arg]
    return redis_client
