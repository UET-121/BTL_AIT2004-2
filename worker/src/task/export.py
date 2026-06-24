import select
import time
import io
import pandas as pd
import asyncio

from minio import Minio
from urllib.parse import urlparse
from minio import Minio
from sqlalchemy import select
from shared.config.logger import log

from shared.db.database import AsyncSessionLocal
from shared.models import DetectionLog, RecognitionLog, User, Profile
from shared.config.config import Config

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


async def fetch_export_data(stmt):
    async with AsyncSessionLocal() as db:
        res = await db.execute(stmt)
        return res.all()


async def process_export_task(payload: dict, bbox_out_queue, log_type: str = "detection"):
    try:
        user_id = payload.get("user_id") or payload.get("requested_by")
        start_date = payload.get("start_date")
        end_date = payload.get("end_date")
        cam_id = payload.get("camera_id")
        log.info(f"Khởi chạy tiến trình xuất báo cáo cho User {user_id} (loại: {log_type})...")

        if log_type == "detection":
            stmt = (
                select(
                    DetectionLog.create_at.label("Thời gian"),
                    DetectionLog.camera_id.label("Mã Camera"),
                    DetectionLog.profile_id.label("ID Theo Vết/Biển số"),
                )
            )
            if start_date and end_date:
                stmt = stmt.where(DetectionLog.create_at.between(start_date, end_date))
            if cam_id:
                stmt = stmt.where(DetectionLog.camera_id == cam_id)
        else:
            profile_id = payload.get("profile_id")
            stmt = (
                select(
                    RecognitionLog.captured_at.label("Thời gian"),
                    RecognitionLog.camera_id.label("Mã Camera"),
                    Profile.name.label("Tên Hồ Sơ"),
                )
                .join(Profile, RecognitionLog.profile_id == Profile.id, isouter=True)
            )
            if start_date and end_date:
                stmt = stmt.where(RecognitionLog.captured_at.between(start_date, end_date))
            if cam_id:
                stmt = stmt.where(RecognitionLog.camera_id == cam_id)
            if profile_id:
                stmt = stmt.where(RecognitionLog.profile_id == profile_id)

        async with AsyncSessionLocal() as db:
            result = await db.execute(stmt)
            rows = result.fetchall()

        if not rows:
            log.warning("Không có dữ liệu trong khoảng thời gian này để xuất.")
            await bbox_out_queue.put(
                {
                    "topic": "ui.export.error",
                    "data": {
                        "user_id": user_id,
                        "message": "Không có dữ liệu nào trong khoảng thời gian hoặc bộ lọc đã chọn.",
                    },
                }
            )
            return

        def build_excel():
            df = pd.DataFrame([dict(r._mapping) for r in rows])
            
            # Xóa bỏ múi giờ để pandas to_excel không bị lỗi
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = df[col].dt.tz_localize(None)
                    
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Báo cáo")
            buf.seek(0)
            return buf

        excel_buffer = await asyncio.get_event_loop().run_in_executor(None, build_excel)

        object_name = f"exports/user_{user_id}/report_{int(time.time())}.xlsx"

        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: minio_client.put_object(
                bucket_name=BUCKET_NAME,
                object_name=object_name,
                data=excel_buffer,
                length=len(excel_buffer.getvalue()),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
        )
        log.info(f"Đã lưu file báo cáo lên MinIO: {object_name}")

        await bbox_out_queue.put(
            {
                "topic": "ui.export.completed",
                "data": {
                    "user_id": user_id,
                    "download_url": f"/api/internal/download/{object_name}",
                    "message": "Xuất báo cáo thành công!",
                },
            }
        )
    except Exception as e:
        log.error(f"Lỗi xuất báo cáo: {e}", exc_info=True)
        await bbox_out_queue.put(
            {
                "topic": "ui.export.error",
                "data": {"user_id": user_id, "message": str(e)},
            }
        )
