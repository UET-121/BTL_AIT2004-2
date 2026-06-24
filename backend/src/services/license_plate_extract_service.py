import base64
from fastapi import UploadFile
from .rpc_client import rpc_client

async def extract_license_plate_service(file: UploadFile) -> str:
    """
    Đọc file ảnh, gửi qua RabbitMQ RPC để trích xuất chữ biển số (OCR).
    """
    contents = await file.read()
    image_base64 = base64.b64encode(contents).decode("utf-8")

    response = await rpc_client.call_extract_license_plate(image_base64)

    if response.get("status") == "success":
        plate_text = response.get("plate_text")
        if not plate_text:
            raise ValueError("Không thể nhận diện chữ từ biển số trong ảnh.")
        return plate_text
    else:
        raise ValueError(response.get("message", "Lỗi không xác định từ AI Worker."))
