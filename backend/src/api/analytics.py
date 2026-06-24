from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_
from datetime import datetime, timezone

from shared.db.database import get_db
from shared.models import (
    DetectionLog as Log,
    User,
)
from ..security.user_manage import viewer_required

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/overview")
async def get_analytics_overview(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(viewer_required)
):
    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=timezone.utc)

    stmt_profiles = select(func.count(User.id))
    res_profiles = await db.execute(stmt_profiles)
    known_profiles = res_profiles.scalar() or 0

    stmt_total = select(func.count(Log.id)).where(Log.create_at >= today_start)
    res_total = await db.execute(stmt_total)
    total_detections = res_total.scalar() or 0

    stmt_unknown = select(func.count(Log.id)).where(
        and_(Log.create_at >= today_start, Log.profile_id == None)
    )
    res_unknown = await db.execute(stmt_unknown)
    unknown_detections = res_unknown.scalar() or 0

    time_format = func.to_char(Log.create_at, "HH24:00")
    stmt_bar = (
        select(time_format.label("time"), func.count(Log.id).label("detections"))
        .where(Log.create_at >= today_start)
        .group_by(time_format)
        .order_by(time_format)
    )
    res_bar = await db.execute(stmt_bar)
    bar_data = [
        {"time": row.time, "detections": row.detections} for row in res_bar.all()
    ]

    stmt_pie = (
        select(Log.camera_id.label("name"), func.count(Log.id).label("value"))
        .where(Log.create_at >= today_start)
        .group_by(Log.camera_id)
    )
    res_pie = await db.execute(stmt_pie)
    pie_data = [
        {"name": f"Cam {row.name}", "value": row.value} for row in res_pie.all()
    ]

    return {
        "total_detections": total_detections,
        "known_profiles": known_profiles,
        "unknown_detections": unknown_detections,
        "bar_data": bar_data,
        "pie_data": pie_data,
    }
