import json
from sqlalchemy.future import select
from cachetools import LRUCache

from shared.db.database import AsyncSessionLocal
from shared.models.profile import Profile
from shared.core.redis import redis_client
from shared.config.logger import log as logger

RAM_PLATE_CACHE = LRUCache(maxsize=1000)


async def sync_plate_to_redis():

    logger.info("[CACHE] Kích hoạt quá trình đồng bộ Biển số lên Redis...")

    async with AsyncSessionLocal() as db:
        try:

            query = select(Profile.id, Profile.license_plate_number).where(
                Profile.license_plate_number.isnot(None)
            )
            result = await db.execute(query)
            profiles = result.all()

            if not profiles:
                logger.warning("[CACHE] Không có biển số nào trong Database.")
                return

            pipeline = redis_client.pipeline()

            pipeline.delete("license_plate_texts_hash")

            local_ram_dict = {}

            for profile_id, plate_text in profiles:
                if not plate_text:
                    continue

                pipeline.hset(
                    "license_plate_texts_hash", plate_text, str(profile_id)
                )

                local_ram_dict[plate_text] = profile_id

            await pipeline.execute()

            RAM_PLATE_CACHE.clear()
            for p_text, p_id in local_ram_dict.items():
                if len(RAM_PLATE_CACHE) >= 1000:
                    break
                RAM_PLATE_CACHE[p_text] = p_id

            logger.info(
                f"[CACHE] Đã đồng bộ {len(profiles)} biển số lên Redis và RAM thành công!"
            )

        except Exception as e:
            logger.error(
                f"[CACHE] Lỗi nghiêm trọng khi đồng bộ Biển số: {e}", exc_info=True
            )
