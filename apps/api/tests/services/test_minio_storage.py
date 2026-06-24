import pytest
from unittest.mock import MagicMock, patch
from app.services.storage import MinioStorage
from app.shared.config import Settings


@pytest.fixture
def mock_settings():
    return Settings(
        STORAGE_TYPE="minio",
        MINIO_URL="http://mock-minio:9000",
        MINIO_ACCESS_KEY="mock-access",
        MINIO_SECRET_KEY="mock-secret",
        MINIO_BUCKET="test-bucket",
    )


@patch("app.services.storage.Minio")
def test_minio_storage_initialization(mock_minio_class, mock_settings):
    mock_minio_client = MagicMock()
    mock_minio_class.return_value = mock_minio_client
    mock_minio_client.bucket_exists.return_value = False

    storage = MinioStorage(mock_settings)

    mock_minio_class.assert_called_once_with(
        endpoint="mock-minio:9000",
        access_key="mock-access",
        secret_key="mock-secret",
        secure=False,
    )
    mock_minio_client.bucket_exists.assert_called_once_with("test-bucket")
    mock_minio_client.make_bucket.assert_called_once_with("test-bucket")


@pytest.mark.asyncio
@patch("app.services.storage.Minio")
async def test_minio_storage_save_get_delete(mock_minio_class, mock_settings):
    mock_minio_client = MagicMock()
    mock_minio_class.return_value = mock_minio_client
    mock_minio_client.bucket_exists.return_value = True

    storage = MinioStorage(mock_settings)

    # Test save
    content = b"test content"
    res = await storage.save("test.mp4", content)
    assert res == "test.mp4"
    assert mock_minio_client.put_object.called

    # Test get_url
    mock_minio_client.presigned_get_object.return_value = "http://mock-minio:9000/test-bucket/test.mp4?signature=xyz"
    url = await storage.get_url("test.mp4")
    assert "signature=xyz" in url
    assert mock_minio_client.presigned_get_object.called

    # Test download
    storage.download_sync("test.mp4", "/tmp/local.mp4")
    mock_minio_client.fget_object.assert_called_once_with("test-bucket", "test.mp4", "/tmp/local.mp4")

    # Test delete
    await storage.delete("test.mp4")
    mock_minio_client.remove_object.assert_called_once_with("test-bucket", "test.mp4")
