import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")
    assert "version" in data


@pytest.mark.asyncio
async def test_upload_valid_png(client: AsyncClient, sample_png_bytes: bytes):
    files = {"file": ("plate.png", sample_png_bytes, "image/png")}
    response = await client.post("/api/v1/recognition", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert data["status"] == "NOT_STARTED"


@pytest.mark.asyncio
async def test_upload_invalid_pdf(client: AsyncClient):
    files = {"file": ("doc.pdf", b"%PDF-1.4 fake", "application/pdf")}
    response = await client.post("/api/v1/recognition", files=files)
    assert response.status_code == 400
    assert "image" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_by_id(client: AsyncClient, sample_jpeg_bytes: bytes):
    upload = await client.post(
        "/api/v1/recognition",
        files={"file": ("plate.jpg", sample_jpeg_bytes, "image/jpeg")},
    )
    request_id = upload.json()["request_id"]

    response = await client.get(f"/api/v1/recognition/{request_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == request_id
    assert data["image_url"].startswith("/uploads/")


@pytest.mark.asyncio
async def test_get_not_found(client: AsyncClient):
    response = await client.get(
        "/api/v1/recognition/550e8400-e29b-41d4-a716-446655440000"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_pagination(client: AsyncClient, sample_png_bytes: bytes):
    for i in range(3):
        await client.post(
            "/api/v1/recognition",
            files={"file": (f"p{i}.png", sample_png_bytes, "image/png")},
        )

    response = await client.get("/api/v1/recognition?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 3
    assert len(data["items"]) == 2
    assert data["total_pages"] >= 2


@pytest.mark.asyncio
async def test_reprocess_invalid_status(client: AsyncClient, sample_png_bytes: bytes, db_session):
    from app.models.recognition import RecognitionRequest, RecognitionStatus
    import uuid

    record = RecognitionRequest(
        id=uuid.uuid4(),
        image_url="/uploads/test.png",
        status=RecognitionStatus.COMPLETED,
        plate_number="ABC1D23",
    )
    db_session.add(record)
    await db_session.commit()

    response = await client.post(f"/api/v1/recognition/{record.id}/reprocess")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_reprocess_needs_review(client: AsyncClient, sample_png_bytes: bytes, db_session):
    from app.models.recognition import RecognitionRequest, RecognitionStatus
    import uuid

    record = RecognitionRequest(
        id=uuid.uuid4(),
        image_url="/uploads/test.png",
        status=RecognitionStatus.NEEDS_REVIEW,
        plate_number="ABC1D23",
        needs_review=True,
    )
    db_session.add(record)
    await db_session.commit()

    response = await client.post(f"/api/v1/recognition/{record.id}/reprocess")
    assert response.status_code == 200
    assert response.json()["status"] == "NOT_STARTED"

