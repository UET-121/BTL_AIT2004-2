import io
import os
import sys

# Default to local storage for integration testing to prevent MinIO client exceptions
os.environ["STORAGE_TYPE"] = "local"
os.environ["UPLOAD_DIR"] = "test_uploads"

from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

# Dynamically mock the minio module to allow running tests without installing it
class MockMinio:
    def __init__(self, *args, **kwargs):
        pass
    def bucket_exists(self, *args, **kwargs):
        return True
    def make_bucket(self, *args, **kwargs):
        pass

mock_minio = MagicMock()
mock_minio.Minio = MockMinio
sys.modules['minio'] = mock_minio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.models.recognition import RecognitionRequest  # noqa: F401
from app.shared.database import Base, get_db

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///:memory:",
)


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest_asyncio.fixture
async def db_engine():
    connect_args = {"check_same_thread": False} if TEST_DATABASE_URL.startswith("sqlite") else {}
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, connect_args=connect_args)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

@pytest_asyncio.fixture
async def client(db_engine) -> AsyncGenerator[AsyncClient, None]:
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sample_png_bytes() -> bytes:
    img = Image.new("RGB", (200, 80), color=(255, 255, 255))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def sample_jpeg_bytes() -> bytes:
    img = Image.new("RGB", (200, 80), color=(128, 128, 128))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()
