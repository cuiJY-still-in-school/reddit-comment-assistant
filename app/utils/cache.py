from typing import Optional
import redis.asyncio as aioredis
from app.config import settings


redis_client: Optional[aioredis.Redis] = None


async def init_redis():
    global redis_client
    redis_client = aioredis.from_url(
        settings.redis_url,
        decode_responses=True,
    )


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()


async def get_redis() -> aioredis.Redis:
    return redis_client


async def cache_get(key: str) -> Optional[str]:
    r = await get_redis()
    return await r.get(key)


async def cache_set(key: str, value: str, ttl: int = 1800):
    r = await get_redis()
    await r.setex(key, ttl, value)


async def cache_delete(key: str):
    r = await get_redis()
    await r.delete(key)
