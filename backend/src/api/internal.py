from urllib.parse import urlparse
from sqlalchemy import text
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from minio import Minio

from shared.db.database import engine
from shared.schemas.camera import CameraStatusUpdate
from shared.models import User
from shared.config.logger import log
from shared.config.config import Config

from ..security.user_manage import get_user_from_url_token

router = APIRouter(prefix="/api/internal", tags=["Internal"])

BUCKET_NAME = Config.MINIO_BUCKET_NAME
MINIO_URL = Config.MINIO_ENDPOINT
MINIO_ACCESS_KEY = Config.MINIO_ACCESS_KEY
MINIO_SECRET_KEY = Config.MINIO_SECRET_KEY

parsed_url = urlparse(MINIO_URL)

endpoint = parsed_url.netloc
is_secure = parsed_url.scheme == "https"

minio_client = Minio(
    endpoint=endpoint,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=is_secure,
)


@router.post("/update_camera_status", include_in_schema=False)
async def update_camera_status(req: CameraStatusUpdate):
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text("UPDATE cameras SET is_active = :status WHERE id = :id"),
                {"status": req.is_active, "id": int(req.camera_id)},
            )
        return {"status": "success"}
    except Exception as e:
        log.error(f"Lỗi DB: {e}")
        return {"status": "error"}


@router.get("/download/{object_name:path}", include_in_schema=False)
async def download_file(
    object_name: str, user: User = Depends(get_user_from_url_token)
):
    try:
        response = minio_client.get_object(
            bucket_name=BUCKET_NAME, object_name=object_name
        )
        filename = object_name.split("/")[-1]
        
        return StreamingResponse(
            response, 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        log.error(f"Lỗi tải file từ MinIO: {e}")
        raise HTTPException(status_code=404, detail="File không tồn tại hoặc đã bị xóa")


@router.get("/{object_name:path}", include_in_schema=False)
async def get_image_proxy(
    object_name: str, user: User = Depends(get_user_from_url_token)
):
    try:
        response = minio_client.get_object(
            bucket_name="license_plate-recognition-images", object_name=object_name
        )

        return StreamingResponse(response, media_type="image/jpeg")

    except Exception as e:
        raise HTTPException(
            status_code=404, detail="Không tìm thấy ảnh hoặc bạn không có quyền xem"
        )
