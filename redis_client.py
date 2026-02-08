import logging
from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis

from config import Config


redis_instance: Redis | None = None
logger = logging.getLogger(__name__)


async def init_redis(
    host: str = Config.REDIS_HOST,
    port: int = Config.REDIS_PORT,
    db: int = Config.REDIS_DB,
    decode_responses: bool = True,
    socket_connect_timeout: int = 5,
    socket_timeout: int = 5,
) -> Redis:
    global redis_instance
    if redis_instance is None:
        redis_instance = Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=decode_responses,
            socket_connect_timeout=socket_connect_timeout,
            socket_timeout=socket_timeout,
            retry_on_timeout=True,
        )
        try:
            await redis_instance.ping()
            logger.info("✅ Redis connected")
        except Exception as e:
            logger.info(f"❌ Redis connection failed: {e}")
            await redis_instance.aclose()
            raise
    return redis_instance


async def get_redis() -> Redis:
    return await init_redis()


RedisDep = Annotated[Redis, Depends(get_redis)]
