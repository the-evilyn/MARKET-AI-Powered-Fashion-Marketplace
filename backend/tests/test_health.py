from unittest.mock import patch
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "AI Fashion Marketplace" in data["app"]
    assert "health" in data


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    # Test root-mounted health endpoint
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app_name"] == "AI Fashion Marketplace"
    assert "version" in data
    assert "timestamp" in data

    # Test api/v1 mounted health endpoint
    response_v1 = await async_client.get("/api/v1/health")
    assert response_v1.status_code == 200
    assert response_v1.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_liveness_endpoint(async_client: AsyncClient):
    response = await async_client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


@pytest.mark.asyncio
async def test_readiness_healthy(async_client: AsyncClient):
    with patch("app.modules.health.routes.check_db_health", return_value=True), \
         patch("app.modules.health.routes.check_redis_health", return_value=True), \
         patch("app.modules.health.routes.check_storage_health", return_value=True):
        response = await async_client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["components"]["database"] == "up"
        assert data["components"]["redis"] == "up"
        assert data["components"]["storage"] == "up"


@pytest.mark.asyncio
async def test_readiness_unhealthy(async_client: AsyncClient):
    with patch("app.modules.health.routes.check_db_health", return_value=False), \
         patch("app.modules.health.routes.check_redis_health", return_value=False), \
         patch("app.modules.health.routes.check_storage_health", return_value=False):
        response = await async_client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["components"]["database"] == "down"
        assert data["components"]["redis"] == "down"
        assert data["components"]["storage"] == "down"
