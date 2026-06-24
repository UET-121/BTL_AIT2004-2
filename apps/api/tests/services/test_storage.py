import pytest

from app.services.storage import LocalStorage


@pytest.mark.asyncio
async def test_local_storage_save_get_delete(tmp_path):
    storage = LocalStorage(str(tmp_path))
    content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20

    url = await storage.save("test.png", content)
    assert url == "/uploads/test.png"
    assert (tmp_path / "test.png").exists()

    assert await storage.get_url("test.png") == "/uploads/test.png"

    await storage.delete("test.png")
    assert not (tmp_path / "test.png").exists()
