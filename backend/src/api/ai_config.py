from fastapi import APIRouter, Body, Depends

from shared.core.redis import redis_client

from ..services.mq_command import CommandPublisher
from ..security.user_manage import admin_required, User

router = APIRouter(prefix="/api/config", tags=["Config"])


from shared.config.config import Config

@router.get("/")
async def get_ai_config(user: User = Depends(admin_required)):
    # Default values from config
    detect_config = await redis_client.hgetall("ai_global_config")
    
    return {
        "conf_thres": float(detect_config.get("conf_thres", 0.5)) if detect_config else 0.5,
        "iou_thres": float(detect_config.get("iou_thres", 0.4)) if detect_config else 0.4,
    }

@router.put("/detect-thresholds")
async def update_ai_thresholds(
    conf_thres: float = None,
    iou_thres: float = None,
    user: User = Depends(admin_required),
):
    await redis_client.hset(
        "ai_global_config",
        mapping={"conf_thres": str(conf_thres), "iou_thres": str(iou_thres)},
    )

    return {"status": "success", "message": "Đã cập nhật cấu hình AI toàn hệ thống."}
