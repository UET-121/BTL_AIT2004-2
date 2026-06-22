from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, and_
from typing import Optional
from datetime import datetime

from shared.db.database import get_db
from shared.models import RecognitionLog, Profile, User

from ..security.user_manage import manager_required

router = APIRouter(prefix="/api/recognition", tags=["Logs"])


@router.get("/get_logs")
async def get_recognition_logs(
    camera_id: Optional[int] = None,
    profile_id: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(manager_required),
):
    query = select(RecognitionLog, Profile.name).outerjoin(
        Profile, RecognitionLog.profile_id == Profile.id
    )

    conditions = []
    if camera_id:
        conditions.append(RecognitionLog.camera_id == camera_id)
    if profile_id:
        conditions.append(RecognitionLog.profile_id == profile_id)
    if start_time:
        conditions.append(RecognitionLog.captured_at >= start_time)
    if end_time:
        conditions.append(RecognitionLog.captured_at <= end_time)

    if conditions:
        query = query.filter(and_(*conditions))

    query = query.order_by(desc(RecognitionLog.captured_at)).offset(skip).limit(limit)

    result = await db.execute(query)

    logs = []
    for log_entry, profile_name in result.all():
        logs.append(
            {
                "log_id": log_entry.id,
                "camera_id": log_entry.camera_id,
                "profile_name": profile_name or "Người lạ",
                "captured_at": log_entry.captured_at,
                "image_url": log_entry.image_url,
            }
        )

    return {"status": "success", "data": logs}


@router.delete("/delete/{log_id}")
async def delete_recognition_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(manager_required),
):
    from sqlalchemy import delete
    from fastapi import HTTPException

    result = await db.execute(select(RecognitionLog).where(RecognitionLog.id == log_id))
    log_entry = result.scalar_one_or_none()

    if not log_entry:
        raise HTTPException(status_code=404, detail="Không tìm thấy log này.")

    await db.execute(delete(RecognitionLog).where(RecognitionLog.id == log_id))
    await db.commit()

    return {"status": "success", "message": f"Đã xóa log {log_id}"}


@router.get("/export")
async def export_recognition_logs(
    camera_id: Optional[int] = Query(None, description="Lọc theo ID Camera"),
    profile_id: Optional[int] = Query(None, description="Lọc theo ID Hồ sơ"),
    start_time: Optional[datetime] = Query(
        None, description="Từ thời gian (Định dạng: YYYY-MM-DDTHH:MM:SS)"
    ),
    end_time: Optional[datetime] = Query(
        None, description="Đến thời gian (Định dạng: YYYY-MM-DDTHH:MM:SS)"
    ),
    user: User = Depends(manager_required),
    db: AsyncSession = Depends(get_db),
):
    from ..services.mq_command import CommandPublisher

    cmd = CommandPublisher()
    cmd.send_recognition_export_command(
        camera_id=camera_id,
        profile_id=profile_id,
        start_time=start_time,
        end_time=end_time,
        requested_by=user.username,
    )
    cmd.close()

    return {
        "status": "success",
        "message": "Yêu cầu xuất dữ liệu đã được gửi. Vui lòng kiểm tra sau vài phút.",
    }
