"""
/api/v1/streams  — Single-stream control API.

Frontend gửi lệnh START/STOP luồng video (RTSP hoặc file).
Trạng thái được lưu trong Redis key "stream:status" dưới dạng hash:
  status        : stopped | starting | running | error
  source        : đường dẫn/URL
  error_message : mô tả lỗi (nếu có)

Commands được gửi sang ai_worker qua RabbitMQ (exchange=system_event_bus).
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel

from shared.core import redis as redis_module
from shared.config.logger import log

from ..services.mq_command import CommandPublisher

router = APIRouter(prefix="/api/v1/streams", tags=["Stream Control"])

STREAM_STATUS_KEY = "stream:status"


# ─── Helpers ────────────────────────────────────────────────────────────────

async def _get_stream_state() -> dict:
    rc = redis_module.redis_client
    data = await rc.hgetall(STREAM_STATUS_KEY)
    return {
        "status": data.get("status", "stopped"),
        "source": data.get("source") or None,
        "error_message": data.get("error_message") or None,
    }


async def _set_stream_state(status: str, source: str = None, error_message: str = None):
    rc = redis_module.redis_client
    mapping = {"status": status}
    if source is not None:
        mapping["source"] = source
    if error_message is not None:
        mapping["error_message"] = error_message
    else:
        mapping["error_message"] = ""
    await rc.hset(STREAM_STATUS_KEY, mapping=mapping)


# ─── Schemas ─────────────────────────────────────────────────────────────────

class StartStreamRequest(BaseModel):
    source: str  # RTSP URL, "0" for webcam, hoặc path video


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/status")
async def get_stream_status():
    """Trả về trạng thái hiện tại của luồng đơn (single stream)."""
    return await _get_stream_state()


@router.post("/start")
async def start_stream(
    body: StartStreamRequest,
):
    """Gửi lệnh START stream tới ai_worker qua RabbitMQ."""
    state = await _get_stream_state()
    if state["status"] in ("running", "starting"):
        raise HTTPException(
            status_code=409,
            detail=f"Luồng đang ở trạng thái '{state['status']}'. Hãy dừng trước."
        )

    try:
        await _set_stream_state("starting", source=body.source)

        cmd_pub = CommandPublisher()
        cmd_pub.send_message(
            {"action": "STREAM_START", "source": body.source},
            routing_key="task.stream.control",
        )
        cmd_pub.close()
        log.info(f"[Streams] Đã gửi lệnh START, nguồn: {body.source}")
    except Exception as e:
        await _set_stream_state("error", error_message=str(e))
        raise HTTPException(status_code=500, detail=f"Không thể gửi lệnh tới AI worker: {e}")

    return await _get_stream_state()


@router.post("/stop")
async def stop_stream():
    """Gửi lệnh STOP stream tới ai_worker qua RabbitMQ."""
    state = await _get_stream_state()
    if state["status"] in ("stopped",):
        return await _get_stream_state()

    try:
        cmd_pub = CommandPublisher()
        cmd_pub.send_message(
            {"action": "STREAM_STOP"},
            routing_key="task.stream.control",
        )
        cmd_pub.close()
        await _set_stream_state("stopped")
        log.info("[Streams] Đã gửi lệnh STOP.")
    except Exception as e:
        log.error(f"[Streams] Lỗi khi gửi STOP: {e}")

    return await _get_stream_state()
