from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, and_
from typing import Optional
from datetime import datetime

from shared.models import DetectionLog


async def get_detection_logs(
    db: AsyncSession,
    camera_id: Optional[int] = None,
    person_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
):
    query = select(DetectionLog)

    conditions = []

    if camera_id is not None:
        conditions.append(DetectionLog.camera_id == camera_id)

    if person_id:
        conditions.append(DetectionLog.person_id.ilike(f"%{person_id}%"))

    if start_time is not None:
        conditions.append(DetectionLog.create_at >= start_time)

    if end_time is not None:
        conditions.append(DetectionLog.create_at <= end_time)

    if conditions:
        query = query.where(and_(*conditions))

    query = query.order_by(DetectionLog.create_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


async def delete_detection_log(db: AsyncSession, log_id: int):

    result = await db.execute(select(DetectionLog).where(DetectionLog.id == log_id))
    log = result.scalar_one_or_none()

    if not log:
        return None

    image_url_to_delete = log.image_url

    await db.execute(delete(DetectionLog).where(DetectionLog.id == log_id))
    await db.commit()

    return image_url_to_delete
