import httpx
from shared.config.logger import log


async def dispatch_webhook_task(
    profile_id: int, camera_id: str, detect_time: str, webhook_url: str
):
    payload = {"profile_id": profile_id, "camera_id": camera_id, "time": detect_time}

    timeout = httpx.Timeout(3.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()
            log.info(
                f"[WEBHOOK SUCCESS] Đã mở cửa cho Profile ID {profile_id} qua {webhook_url}"
            )

    except httpx.HTTPStatusError as exc:
        log.error(
            f"[WEBHOOK ERROR] Phản hồi lỗi từ Server ngoại vi: {exc.response.status_code}"
        )
    except httpx.RequestError as exc:
        log.error(f"[WEBHOOK ERROR] Không thể kết nối tới URL khóa từ: {exc}")
