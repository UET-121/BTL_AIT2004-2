from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks

from urllib.parse import urlparse
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.user import User
from shared.core.storage import delete_images_from_minio
from shared.db.database import get_db
from shared.config.logger import log
from shared.config.config import Config

from ..security.user_manage import viewer_required, manager_required
from ..crud.detection import (
    get_detection_logs,
    delete_detection_log,
)
from ..services.mq_command import CommandPublisher

BUCKET_NAME = Config.MINIO_BUCKET_NAME


router = APIRouter(prefix="/api/detection", tags=["Detect Log"])


@router.get("/get_log")
async def read_detections(
    camera_id: Optional[int] = Query(None, description="Lọc theo ID Camera"),
    start_time: Optional[datetime] = Query(
        None, description="Từ thời gian (Định dạng: YYYY-MM-DDTHH:MM:SS)"
    ),
    end_time: Optional[datetime] = Query(
        None, description="Đến thời gian (Định dạng: YYYY-MM-DDTHH:MM:SS)"
    ),
    skip: int = Query(0, ge=0, description="Số lượng bản ghi bỏ qua"),
    limit: int = Query(100, ge=1, le=1000, description="Giới hạn số bản ghi trả về"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(viewer_required),
):
    logs = await get_detection_logs(
        db=db,
        camera_id=camera_id,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit,
    )

    return {"status": "success", "count": len(logs), "data": logs}


@router.delete("/delete/{log_id}")
async def delete_log(
    log_id: int,
    background_tasks: BackgroundTasks,
    user: User = Depends(manager_required),
    db: AsyncSession = Depends(get_db),
):
    image_url = await delete_detection_log(db, log_id)

    if not image_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy lịch sử nhận diện này.",
        )

    object_key = None
    path = urlparse(image_url).path
    prefix_to_remove = f"/{BUCKET_NAME}/"

    if path.startswith(prefix_to_remove):
        object_key = path[len(prefix_to_remove) :]

    if object_key:
        background_tasks.add_task(delete_images_from_minio, BUCKET_NAME, [object_key])

    log.info(
        f"Admin '{user.username}' đã xóa log {log_id}. Ảnh đang được dọn dẹp ngầm."
    )

    return {
        "status": "success",
        "message": f"Admin '{user.username}' đã xóa thành công log {log_id} và ảnh tương ứng.",
    }


@router.get("/export")
async def export_logs(
    camera_id: Optional[int] = Query(None, description="Lọc theo ID Camera"),
    start_time: Optional[datetime] = Query(
        None, description="Từ thời gian (Định dạng: YYYY-MM-DDTHH:MM:SS)"
    ),
    end_time: Optional[datetime] = Query(
        None, description="Đến thời gian (Định dạng: YYYY-MM-DDTHH:MM:SS)"
    ),
    user: User = Depends(viewer_required),
    db: AsyncSession = Depends(get_db),
):
    cmd = CommandPublisher()
    cmd.send_export_command(
        camera_id=camera_id,
        start_time=start_time,
        end_time=end_time,
        requested_by=user.username,
    )
    cmd.close()

    return {
        "status": "success",
        "message": "Yêu cầu xuất dữ liệu đã được gửi. Vui lòng kiểm tra sau vài phút.",
    }
