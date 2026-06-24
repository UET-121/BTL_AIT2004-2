import time
import asyncio

from datetime import datetime, timedelta, timezone
from fastapi import (
    FastAPI,
    Depends,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, delete
from sqlalchemy.future import select
from contextlib import asynccontextmanager

from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from shared.db.database import get_db, engine, Base, AsyncSessionLocal
from shared.config.logger import log
from shared.core.redis import redis_client
from shared.models import Camera, RecognitionLog

from .api.streams import router as streams_router
from .api.recognition_api import router as recognition_api_router
from .middleware.rate_limit import limiter

from .services.rabbitmq import init_rabbitmq, close_rabbitmq
from .services.mqlistener import start_ui_notification_listener
from .services.websocket_manager import ws_manager
from .services.mediamtx_client import mediamtx
from .services.rpc_client import rpc_client
from .security.user_manage import init_default_users


async def auto_cleanup_logs_task(retention_days: int = 30):

    log.info(
        f"[*] Đã kích hoạt luồng dọn dẹp Log tự động (Giữ lại {retention_days} ngày)."
    )

    while True:
        try:
            async with AsyncSessionLocal() as db:
                threshold_date = datetime.now(timezone.utc).replace(
                    tzinfo=None
                ) - timedelta(days=retention_days)

                stmt = delete(RecognitionLog).where(
                    RecognitionLog.captured_at < threshold_date
                )

                result = await db.execute(stmt)
                await db.commit()

                if result.rowcount > 0:
                    log.info(
                        f"[CRON] Hệ thống đã tự động dọn dẹp {result.rowcount} bản ghi log nhận diện cũ hơn {retention_days} ngày."
                    )
        except Exception as e:
            log.error(f"[CRON] Lỗi xảy ra trong tiến trình dọn dẹp log: {e}")
        await asyncio.sleep(86400)


async def sync_camera_status_task():
    log.info("[*] Đã bật luồng kiểm tra trạng thái Camera ngầm (Watchdog) - 60s/lần")
    while True:
        await asyncio.sleep(60)
        try:
            if redis_client is None:
                continue

            async with AsyncSessionLocal() as db:

                result = await db.execute(
                    text("SELECT id FROM cameras WHERE is_active = True")
                )
                active_cameras = result.scalars().all()

                for cam_id in active_cameras:
                    heartbeat_exists = await redis_client.exists(f"heartbeat:{cam_id}")

                    if not heartbeat_exists:
                        log.warning(
                            f"[*] Phát hiện camera {cam_id} bị sập ngầm (Mất Heartbeat). Đang fix DB..."
                        )

                        await db.execute(
                            text("UPDATE cameras SET is_active = False WHERE id = :id"),
                            {"id": cam_id},
                        )
                        await db.commit()

                        await ws_manager.broadcast(
                            {
                                "topic": "ui.camera.disconnected",
                                "data": {
                                    "camera_id": str(cam_id),
                                    "message": f"Hệ thống phát hiện luồng AI của camera {cam_id} đã dừng đột ngột.",
                                    "is_active": False,
                                },
                            }
                        )

        except Exception as e:
            log.error(f"Lỗi vòng lặp đối soát Watchdog: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.sleep(1)
    await init_rabbitmq()
    listener_task = asyncio.create_task(start_ui_notification_listener())
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    cleanup_task = asyncio.create_task(auto_cleanup_logs_task(retention_days=30))
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Camera).where(Camera.is_active == True))
        active_cameras = result.scalars().all()

        for cam in active_cameras:
            await mediamtx.add_camera_stream(cam.id, cam.url)
        await init_default_users(db)
    await redis_client.init()
    await rpc_client.connect()
    sync_task = asyncio.create_task(sync_camera_status_task())
    yield

    sync_task.cancel()
    listener_task.cancel()
    cleanup_task.cancel()
    if rpc_client.connection:
        await rpc_client.connection.close()
    await close_rabbitmq()
    await redis_client.close()


app = FastAPI(lifespan=lifespan)
Instrumentator().instrument(app).expose(app)

# ─── Rate Limiting ───────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Trả về JSON 429 thân thiện thay vì plaintext mặc định của slowapi."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": f"Quá nhiều yêu cầu. Vui lòng thử lại sau.",
            "retry_after": str(exc.retry_after) if hasattr(exc, "retry_after") else "60",
        },
        headers={"Retry-After": "60"},
    )
# ────────────────────────────────────────────────────────────────────────────

origins = [
    "http://localhost:3000",  # Dành cho React/Next.js
    "http://localhost:5173",  # Dành cho Vite/Vue
    "https://ddlc.me",
    "https://www.ddlc.me",
    "http://ddlc.me",
    "http://www.ddlc.me",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(streams_router)
app.include_router(recognition_api_router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000

    log.info(
        f"API Request",
        extra={
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "duration_ms": f"{process_time:.2f}ms",
        },
    )

    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error(f"Lỗi hệ thống chưa xác định: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)},
    )


@app.get("/test-db")
async def test_database_connection(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT version();"))
        version = result.scalar()
        return {"Success, db_version": version}
    except Exception as e:
        return {"Error:": str(e)}


@app.websocket("/ws/notifications/")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            try:
                data = await websocket.receive_text()
            except WebSocketDisconnect:
                break
            except Exception:
                break
    finally:
        ws_manager.disconnect(websocket)


# ─── WebSocket Live: stream real-time frames + plate detection events ─────────
# ai_worker gửi frames base64 + events qua RabbitMQ → mqlistener broadcast
# Tất cả clients kết nối /ws/live đều nhận được cùng một luồng.
@app.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            try:
                await websocket.receive_text()  # giữ kết nối; client không cần gửi data
            except WebSocketDisconnect:
                break
            except Exception:
                break
    finally:
        ws_manager.disconnect(websocket)
