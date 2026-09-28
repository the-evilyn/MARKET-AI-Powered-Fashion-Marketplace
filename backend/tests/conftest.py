import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import get_settings, Settings


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def settings() -> Settings:
    return get_settings()


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
