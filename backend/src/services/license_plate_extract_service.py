from fastapi import UploadFile
import base64
import io
from PIL import Image

from .rpc_client import rpc_client


async def extract_license_plate_vector_service(file: UploadFile) -> list:

    image_data = await file.read()
    img = Image.open(io.BytesIO(image_data))
    buffered = io.BytesIO()
    img.convert("RGB").save(buffered, format="JPEG", quality=80)
    image_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    result = await rpc_client.call_extract_vector(image_b64)

    if result.get("status") == "error":
        raise ValueError(result.get("message"))

    return result.get("vector")
