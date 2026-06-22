# routers/webhook.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from shared.db.database import get_db
from shared.models import WebhookConfig, User
from ..security.user_manage import admin_required

router = APIRouter(prefix="/api/webhook", tags=["Webhook"])


class WebhookUpdate(BaseModel):
    url: str
    is_active: bool = True


@router.get("/config")
async def get_webhook_config(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(admin_required)
):
    result = await db.execute(select(WebhookConfig).limit(1))
    config = result.scalar_one_or_none()
    if not config:
        return {"url": "", "is_active": False}
    return {"url": config.url, "is_active": config.is_active}


@router.post("/config")
async def update_webhook_config(
    payload: WebhookUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    result = await db.execute(select(WebhookConfig).limit(1))
    config = result.scalar_one_or_none()

    if config:
        config.url = payload.url
        config.is_active = payload.is_active
    else:
        new_config = WebhookConfig(url=payload.url, is_active=payload.is_active)
        db.add(new_config)

    await db.commit()
    return {"message": "Đã lưu cấu hình Webhook thành công."}
