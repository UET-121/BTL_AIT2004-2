import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.routes import router as recognition_router, streams_router, ws_router
from app.logger import configure_logging
from app.models.schemas import HealthResponse
from app.shared.config import get_settings
from app.shared.database import engine

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    
    # Eager-load ML models at application startup to reduce latency on first frame
    from app.services.factories import preload_ml_components
    preload_ml_components()

    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    logger.info("Application startup complete; upload_dir=%s", upload_path)
    yield
    # Stop any active streams on application shutdown to release capture devices
    from app.realtime.manager import stream_manager
    stream_manager.stop_stream()
    await engine.dispose()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="License Plate Recognition API",
    description="Brazilian license plate recognition — async ML pipeline",
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(recognition_router)
app.include_router(streams_router)
app.include_router(ws_router)


upload_path = Path(settings.upload_dir)
upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    db_status = "connected"

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        logger.warning("DB health check failed: %s", exc)
        db_status = "disconnected"

    overall = "ok" if db_status == "connected" else "degraded"
    return HealthResponse(
        status=overall,
        db=db_status,
        redis=None,
        version=settings.app_version,
    )
