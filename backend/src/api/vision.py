from fastapi import APIRouter, HTTPException, File, UploadFile, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from fastapi import APIRouter, HTTPException

from shared.config.logger import log
from shared.db.database import AsyncSession, get_db
from shared.models import Camera
from shared.schemas.camera import CameraStreamRequest, CameraUpdateRequest
from shared.core import redis as redis_module

from ..services.license_plate_extract_service import extract_license_plate_service
from ..services.mq_command import CommandPublisher
from ..security.user_manage import User, admin_required, manager_required
from ..services.mediamtx_client import mediamtx

router = APIRouter(prefix="/api/cameras", tags=["Cameras"])


async def is_in_cooldown(person_id: str, seconds=10):
    key = f"cooldown:{person_id}"
    if redis_module.redis_client is None:
        log.warning("Redis client chưa được khởi tạo, bỏ qua kiểm tra cooldown.")
        return False
    is_new = await redis_module.redis_client.set(key, "1", ex=seconds, nx=True)
    return not is_new


@router.post("/process-image")
async def check_image_validity(file: UploadFile = File(...)):
    try:
        plate_text = await extract_license_plate_service(file)
        return {
            "status": "success",
            "message": "Ảnh hợp lệ, đã tìm thấy biển số!",
            "plate_text": plate_text,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/cameras-list")
async def get_cameras_list(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(manager_required),
):
    try:
        result = await db.execute(select(Camera).order_by(Camera.id))
        cameras = result.scalars().all()

        camera_list = []
        for cam in cameras:
            camera_list.append(
                {
                    "id": str(cam.id),
                    "name": cam.name,
                    "url": cam.url,
                    "is_active": cam.is_active,
                }
            )

        return {"status": "success", "total": len(camera_list), "data": camera_list}

    except Exception as e:
        return {"status": "error", "message": f"Lỗi truy vấn: {str(e)}"}


@router.post("/create-cameras", status_code=201)
async def create_camera(
    request: CameraStreamRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(manager_required),
):
    try:
        new_camera = Camera(
            id=int(request.camera_id),
            url=request.link,
            name=request.name,
            is_active=False,
        )
        db.add(new_camera)
        await db.commit()

        return {
            "status": "success",
            "message": f"Đã lưu cấu hình camera {request.name}",
        }

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Camera ID {request.camera_id} đã tồn tại trong hệ thống.",
        )

@router.put("/update-camera")
async def update_camera(
    camera_id: str,
    request: CameraUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(manager_required),
):
    result = await db.execute(select(Camera).where(Camera.id == int(camera_id)))
    camera = result.scalars().first()

    if not camera:
        raise HTTPException(
            status_code=404, detail="Không tìm thấy Camera trong hệ thống"
        )
        
    camera.url = request.link
    camera.name = request.name
    await db.commit()
    
    return {"status": "success", "message": f"Cập nhật thành công camera {request.name}"}


@router.post("/start-camera", status_code=status.HTTP_202_ACCEPTED)
async def start_camera_stream(
    camera_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(manager_required),
):
    result = await db.execute(select(Camera).where(Camera.id == int(camera_id)))
    camera = result.scalars().first()

    if not camera:
        raise HTTPException(
            status_code=404, detail="Không tìm thấy Camera trong hệ thống"
        )

    existing_pid = await redis_module.redis_client.get(f"stream_pid:{camera_id}")
    if existing_pid:
        return {
            "status": "error",
            "message": f"Camera {camera_id} đang hoạt động rồi!",
        }

    try:

        await mediamtx.add_camera_stream(camera.id, camera.url)

        cmd_pub = CommandPublisher()
        cmd_pub.send_camera_command(
            action="START",
            camera_id=str(camera_id),
            link=f"rtsp://mediamtx:8554/cam_{camera_id}",
        )
        cmd_pub.close()

        return {
            "status": "processing",
            "message": f"Đã gửi lệnh bật Camera {camera_id}. Vui lòng đợi AI xử lý...",
        }

    except Exception as e:
        log.error(f"Lỗi khi khởi động camera {camera_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Lỗi hệ thống khi khởi động Camera")


@router.post("/stop-camera")
async def stop_camera_stream(
    camera_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(manager_required),
):
    result = await db.execute(select(Camera).where(Camera.id == int(camera_id)))
    camera = result.scalar_one_or_none()

    if not camera:
        raise HTTPException(status_code=404, detail="Không tìm thấy Camera.")

    camera.is_active = False
    await db.commit()

    cmd_pub = CommandPublisher()
    cmd_pub.send_camera_command(action="STOP", camera_id=camera_id)
    cmd_pub.close()

    await mediamtx.remove_camera_stream(int(camera_id))

    await redis_module.redis_client.delete(f"stream_pid:{camera_id}")
    await redis_module.redis_client.delete(f"heartbeat:{camera_id}")


@router.post("/delete-camera")
async def delete_camera(
    camera_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(admin_required),
):
    result = await db.execute(select(Camera).where(Camera.id == int(camera_id)))
    camera = result.scalars().first()

    if not camera:
        raise HTTPException(
            status_code=404, detail="Không tìm thấy Camera trong hệ thống"
        )

    existing_pid = await redis_module.redis_client.get(f"stream_pid:{camera_id}")
    if existing_pid:
        cmd_pub = CommandPublisher()
        cmd_pub.send_camera_command(action="STOP", camera_id=camera_id)
        cmd_pub.close()
        log.info(f"Đã gửi lệnh STOP cho camera {camera_id}")

    await mediamtx.remove_camera_stream(int(camera_id))
    await db.delete(camera)
    await db.commit()

    await redis_module.redis_client.delete(f"stream_pid:{camera_id}")
    await redis_module.redis_client.delete(f"heartbeat:{camera_id}")

    await db.delete(camera)
    await db.commit()
    return {"status": "success", "message": f"Đã xóa hoàn toàn camera {camera_id}"}
