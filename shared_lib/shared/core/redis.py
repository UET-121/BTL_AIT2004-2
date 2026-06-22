import redis.asyncio as redis

from shared.config.logger import log
from shared.config.config import config

REDIS_URL = config.REDIS_URL


class RedisClient:
    def __init__(self):
        self._client = None

    async def init(self):
        try:
            self._client = redis.from_url(
                REDIS_URL, encoding="utf-8", decode_responses=True
            )
            await self._client.ping()
            log.info("[✓] Đã kết nối thành công tới Redis")
        except Exception as e:
            log.error(f"[X] Lỗi khởi tạo Redis: {e}")

    async def close(self):
        if self._client:
            await self._client.close()

    def __getattr__(self, name):
        if self._client is None:
            raise RuntimeError(
                f"Redis not initialized. Call await redis_client.init() first."
            )
        return getattr(self._client, name)


redis_client = RedisClient()
