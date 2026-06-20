import logging
import time

from celery import Celery
from celery.signals import worker_process_init

from app.shared.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

celery_app = Celery("plate_recognition")
celery_app.conf.update(
    broker_url=settings.redis_url,
    result_backend=settings.redis_url,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

celery_app.autodiscover_tasks(["app.worker"])


@worker_process_init.connect
def init_worker_models(**kwargs) -> None:
    """Eager-load ML models at worker startup for predictable latency."""
    start = time.perf_counter()
    try:
        from app.services.factories import preload_ml_components

        preload_ml_components()
        elapsed = time.perf_counter() - start
        logger.info("ML components preloaded in %.2fs", elapsed)
    except Exception as exc:
        logger.error("Failed to preload ML components: %s", exc)
        if settings.fail_fast_on_missing_model:
            raise
