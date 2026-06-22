from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    Depends,
    HTTPException,
    Query,
    BackgroundTasks,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from typing import Optional
from urllib.parse import urlparse

from ..services.license_plate_extract_service import extract_license_plate_vector_service
from ..services.mq_command import CommandPublisher
from ..security.user_manage import manager_required, admin_required

from shared.core.storage import delete_images_from_minio
from shared.db.database import get_db
from shared.models import Profile, RecognitionLog, User
from shared.config.config import Config

BUCKET_NAME = Config.MINIO_BUCKET_NAME

router = APIRouter(prefix="/api/profiles", tags=["Profiles"])


@router.post("/create-new-profile")
async def create_new_profile(
    name: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(manager_required),
):
    try:
        vector_data = await extract_license_plate_vector_service(file)
        if len(vector_data) == 0:
            raise HTTPException(
                status_code=404, detail="Không nhận diện được biển số trong ảnh"
            )
        new_profile = Profile(name=name, license_plate_embedding=vector_data)
        db.add(new_profile)
        await db.commit()

        cmd_pub = CommandPublisher()
        cmd_pub.send_reload_cache_signal()
        cmd_pub.close()

        return {"status": "success", "message": f"Đã thêm hồ sơ nhân viên: {name}"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")


@router.get("/get-profile-list")
async def get_all_profiles(
    search: Optional[str] = Query(None, description="Tìm kiếm theo tên"),
    skip: int = Query(0, ge=0, description="Số bản ghi bỏ qua (Phân trang)"),
    limit: int = Query(20, ge=1, le=100, description="Số bản ghi tối đa trả về"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(manager_required),
):
    try:
        query = select(Profile)

        if search:
            query = query.filter(Profile.name.ilike(f"%{search}%"))

        query = query.order_by(desc(Profile.id)).offset(skip).limit(limit)

        result = await db.execute(query)
        profiles = result.scalars().all()

        profile_list = []
        for p in profiles:
            profile_list.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "created_at": (
                        p.created_at.strftime("%Y-%m-%d %H:%M:%S")
                        if p.created_at
                        else None
                    ),
                }
            )

        return {"status": "success", "count": len(profile_list), "data": profile_list}

    except Exception as e:
        return {"status": "error", "message": f"Lỗi máy chủ: {str(e)}"}


@router.delete("/delete-profile")
async def delete_profile(
    profile_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(manager_required),
):
    try:
        profile = await db.get(Profile, profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ")

        log_query = select(RecognitionLog.image_url).where(
            RecognitionLog.profile_id == profile_id
        )
        log_result = await db.execute(log_query)
        image_urls = log_result.scalars().all()

        object_keys_to_delete = []
        for url in image_urls:
            if url:
                path = urlparse(url).path

                prefix_to_remove = f"/{BUCKET_NAME}/"
                if path.startswith(prefix_to_remove):
                    object_key = path[len(prefix_to_remove) :]
                    object_keys_to_delete.append(object_key)

        await db.delete(profile)
        await db.commit()

        if object_keys_to_delete:
            background_tasks.add_task(
                delete_images_from_minio,
                bucket_name=BUCKET_NAME,
                object_keys=object_keys_to_delete,
            )

        cmd_pub = CommandPublisher()
        cmd_pub.send_reload_cache_signal()
        cmd_pub.close()

        return {
            "status": "success",
            "message": "Đã xóa hồ sơ và dọn dẹp ổ cứng an toàn.",
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
