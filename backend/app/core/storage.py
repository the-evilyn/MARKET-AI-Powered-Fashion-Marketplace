import logging
from typing import Optional
from minio import Minio
from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

_minio_client: Optional[Minio] = None


def get_storage_client() -> Minio:
    """Get or create singleton MinIO storage client."""
    global _minio_client
    if _minio_client is None:
        _minio_client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
    return _minio_client


def check_storage_health() -> bool:
    """Check if MinIO object storage is reachable."""
    try:
        client = get_storage_client()
        # bucket_exists or list_buckets is a fast check
        client.bucket_exists(settings.MINIO_BUCKET)
        return True
    except Exception as e:
        logger.warning(f"MinIO storage health check failed: {e}")
        return False
