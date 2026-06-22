import json
import numpy as np
from sqlalchemy.future import select
from cachetools import LRUCache

from shared.db.database import AsyncSessionLocal
from shared.models.profile import Profile
from shared.core.redis import redis_client
from shared.config.logger import log as logger

RAM_FACE_CACHE = LRUCache(maxsize=1000)


async def sync_vector_to_redis():

    logger.info("[CACHE] Kích hoạt quá trình đồng bộ Vector toàn hệ thống...")

    async with AsyncSessionLocal() as db:
        try:

            query = select(Profile.id, Profile.license_plate_embedding).where(
                Profile.license_plate_embedding.isnot(None)
            )
            result = await db.execute(query)
            profiles = result.all()

            if not profiles:
                logger.warning("[CACHE] Không có vector biển số nào trong Database.")
                return

            pipeline = redis_client.pipeline()

            pipeline.delete("license_plate_vectors_hash")

            local_ram_dict = {}

            for profile_id, vector_data in profiles:
                if isinstance(vector_data, str):
                    vector_list = json.loads(vector_data)
                else:
                    vector_list = vector_data

                pipeline.hset(
                    "license_plate_vectors_hash", str(profile_id), json.dumps(vector_list)
                )

                local_ram_dict[profile_id] = np.array(vector_list, dtype=np.float32)

            await pipeline.execute()

            RAM_FACE_CACHE.clear()
            for p_id, vec in local_ram_dict.items():
                if len(RAM_FACE_CACHE) >= 1000:
                    break
                RAM_FACE_CACHE[p_id] = vec

            logger.info(
                f"[CACHE] Đã đồng bộ {len(profiles)} biển số lên Redis và RAM thành công!"
            )

        except Exception as e:
            logger.error(
                f"[CACHE] Lỗi nghiêm trọng khi đồng bộ Vector: {e}", exc_info=True
            )
