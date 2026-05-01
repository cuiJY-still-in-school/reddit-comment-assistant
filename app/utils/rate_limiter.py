from datetime import datetime
from typing import Optional
import redis.asyncio as aioredis
from app.config import settings
from app.utils.cache import get_redis


class RateLimiter:
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client

    async def is_allowed(self, key: str, limit: int, window_seconds: int = 60) -> bool:
        now = datetime.utcnow().timestamp()
        window_key = f"ratelimit:{key}:{int(now // window_seconds)}"

        count = await self.redis.incr(window_key)
        if count == 1:
            await self.redis.expire(window_key, window_seconds)

        return count <= limit


rate_limiter: Optional[RateLimiter] = None


async def init_rate_limiter():
    global rate_limiter
    redis_client = await get_redis()
    rate_limiter = RateLimiter(redis_client)


def get_rate_limiter() -> RateLimiter:
    if rate_limiter is None:
        raise RuntimeError("Rate limiter not initialized")
    return rate_limiter
