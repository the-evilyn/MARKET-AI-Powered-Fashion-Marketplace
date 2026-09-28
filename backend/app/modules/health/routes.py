import asyncio
from fastapi import APIRouter, Response, status
from app.core.config import get_settings
from app.core.database import check_db_health
from app.core.redis import check_redis_health
from app.core.storage import check_storage_health
from app.modules.health.schemas import (
    HealthCheckResponse,
    ReadinessResponse,
    LivenessResponse,
)

router = APIRouter(prefix="/health", tags=["Health & Diagnostics"])
settings = get_settings()


@router.get("", response_model=HealthCheckResponse, summary="Basic service health")
async def get_health() -> HealthCheckResponse:
    """Return basic health status of the API service."""
    return HealthCheckResponse(
        status="ok",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
    )


@router.get("/ready", response_model=ReadinessResponse, summary="Readiness check for backing services")
async def get_readiness(response: Response) -> ReadinessResponse:
    """Check readiness of dependencies: PostgreSQL, Redis, and MinIO storage."""
    db_ok_task = check_db_health()
    redis_ok_task = check_redis_health()
    # MinIO health check is synchronous, run in executor
    loop = asyncio.get_running_loop()
    storage_ok_task = loop.run_in_executor(None, check_storage_health)

    db_ok, redis_ok, storage_ok = await asyncio.gather(
        db_ok_task, redis_ok_task, storage_ok_task
    )

    components = {
        "database": "up" if db_ok else "down",
        "redis": "up" if redis_ok else "down",
        "storage": "up" if storage_ok else "down",
    }

    # Core dependencies required for readiness are database and redis
    all_ready = db_ok and redis_ok
    if not all_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status="ready" if all_ready else "not_ready",
        components=components,
    )


@router.get("/live", response_model=LivenessResponse, summary="Process liveness probe")
async def get_liveness() -> LivenessResponse:
    """Liveness probe to confirm that the server process is responsive."""
    return LivenessResponse(status="alive")
