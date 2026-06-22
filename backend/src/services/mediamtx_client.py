import httpx
from shared.config.logger import log


class MediaMTXClient:
    def __init__(self):
        self.api_url = "http://mediamtx:9997/v3/config/paths"

    async def add_camera_stream(self, camera_id: int, stream_url: str):
        path_name = f"cam_{camera_id}"

        payload = {
            "source": stream_url,
            "sourceOnDemand": False,
            "sourceProtocol": "tcp",
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_url}/add/{path_name}", json=payload
                )
                if response.status_code == 200:
                    log.info(
                        f"[MediaMTX] Đã auto-map thành công luồng {stream_url} vào cam_{camera_id}"
                    )
                else:
                    log.warning(f"[MediaMTX] Lỗi: {response.text}")
            except Exception as e:
                log.error(f"[MediaMTX] Lỗi kết nối: {e}")

    async def remove_camera_stream(self, camera_id: int):
        path_name = f"cam_{camera_id}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.delete(f"{self.api_url}/delete/{path_name}")
                if response.status_code == 200:
                    log.info(f"[MediaMTX] Đã ngắt kết nối luồng {path_name}")
            except Exception as e:
                log.error(f"[MediaMTX] Lỗi khi xóa luồng: {e}")


mediamtx = MediaMTXClient()
