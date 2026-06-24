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
async def test_upload_valid_video(client: AsyncClient):
    files = {"file": ("video.mp4", b"fake video bytes", "video/mp4")}
    response = await client.post("/api/v1/recognition", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert data["status"] == "PENDING"


@pytest.mark.asyncio
async def test_upload_invalid_pdf(client: AsyncClient):
    files = {"file": ("doc.pdf", b"%PDF-1.4 fake", "application/pdf")}
    response = await client.post("/api/v1/recognition", files=files)
    assert response.status_code == 400
    assert "video" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_by_id(client: AsyncClient):
    upload = await client.post(
        "/api/v1/recognition",
        files={"file": ("video.mp4", b"fake video bytes", "video/mp4")},
    )
    request_id = upload.json()["request_id"]

    response = await client.get(f"/api/v1/recognition/{request_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == request_id
    assert data["image_url"].startswith("/uploads/") or "uploads" in data["image_url"]


@pytest.mark.asyncio
async def test_get_not_found(client: AsyncClient):
    response = await client.get(
        "/api/v1/recognition/550e8400-e29b-41d4-a716-446655440000"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_pagination(client: AsyncClient):
    for i in range(3):
        await client.post(
            "/api/v1/recognition",
            files={"file": (f"v{i}.mp4", b"fake video bytes", "video/mp4")},
        )

    response = await client.get("/api/v1/recognition?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 3
    assert len(data["items"]) == 2
    assert data["total_pages"] >= 2



@pytest.mark.asyncio
async def test_delete_request(client: AsyncClient):
    upload = await client.post(
        "/api/v1/recognition",
        files={"file": ("video.mp4", b"fake video bytes", "video/mp4")},
    )
    request_id = upload.json()["request_id"]

    response = await client.delete(f"/api/v1/recognition/{request_id}")
    assert response.status_code == 204
    assert response.content == b""

    get_response = await client.get(f"/api/v1/recognition/{request_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_completed_request(client: AsyncClient, db_session):
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

    response = await client.delete(f"/api/v1/recognition/{record.id}")
    assert response.status_code == 204

    get_response = await client.get(f"/api/v1/recognition/{record.id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_request_not_found(client: AsyncClient):
    response = await client.delete(
        "/api/v1/recognition/550e8400-e29b-41d4-a716-446655440000"
    )
    assert response.status_code == 404

