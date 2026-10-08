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
        client.bucket_exists(settings.MINIO_BUCKET)
        return True
    except Exception as e:
        logger.warning(f"MinIO storage health check failed: {e}")
        return False


# Maximum file size: 10 MB
MAX_IMAGE_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def validate_image_file(content: bytes, filename: Optional[str], content_type: Optional[str]) -> str:
    """
    Validate an uploaded image file strictly against size, MIME type, and magic bytes.
    Returns normalized file extension (e.g. '.jpg', '.png', '.webp').
    Raises HTTPException (400) if validation fails.
    """
    from fastapi import HTTPException, status

    if not content or len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if len(content) > MAX_IMAGE_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {MAX_IMAGE_FILE_SIZE // (1024 * 1024)}MB.",
        )

    # 1. Content-type check
    normalized_mime = (content_type or "").lower().split(";")[0].strip()
    if normalized_mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported media MIME type '{normalized_mime}'. Allowed: JPEG, PNG, WebP.",
        )

    # 2. Magic byte signatures check
    is_valid_magic = False
    detected_ext = ALLOWED_MIME_TYPES[normalized_mime]

    if normalized_mime == "image/jpeg":
        # JPEG starts with FF D8 FF
        if content.startswith(b"\xff\xd8\xff"):
            is_valid_magic = True
    elif normalized_mime == "image/png":
        # PNG starts with 89 50 4E 47 0D 0A 1A 0A
        if content.startswith(b"\x89PNG\r\n\x1a\n"):
            is_valid_magic = True
    elif normalized_mime == "image/webp":
        # WebP starts with RIFF....WEBP
        if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
            is_valid_magic = True

    if not is_valid_magic:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content header does not match declared image format (invalid magic bytes).",
        )

    return detected_ext


class StorageService:
    """Service layer for MinIO object storage interactions."""

    @staticmethod
    def ensure_bucket_exists(bucket_name: Optional[str] = None) -> None:
        """Ensure that the target MinIO bucket exists, creating it if necessary."""
        bucket = bucket_name or settings.MINIO_BUCKET
        client = get_storage_client()
        try:
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
        except Exception as e:
            logger.error(f"Error checking or creating MinIO bucket '{bucket}': {e}")

    @staticmethod
    def upload_file(
        data: bytes,
        object_key: str,
        content_type: str,
        bucket_name: Optional[str] = None,
    ) -> str:
        """
        Upload binary payload to MinIO and return full public URL.
        """
        import io
        bucket = bucket_name or settings.MINIO_BUCKET
        client = get_storage_client()

        StorageService.ensure_bucket_exists(bucket)

        client.put_object(
            bucket_name=bucket,
            object_name=object_key,
            data=io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )

        return StorageService.get_file_url(object_key, bucket)

    @staticmethod
    def get_file_url(object_key: str, bucket_name: Optional[str] = None) -> str:
        """Generate public HTTP URL for an object key."""
        bucket = bucket_name or settings.MINIO_BUCKET
        proto = "https" if settings.MINIO_USE_SSL else "http"
        return f"{proto}://{settings.MINIO_ENDPOINT}/{bucket}/{object_key}"

    @staticmethod
    def delete_file(object_key: str, bucket_name: Optional[str] = None) -> bool:
        """Delete an object from MinIO gracefully."""
        if not object_key:
            return False
        bucket = bucket_name or settings.MINIO_BUCKET
        client = get_storage_client()
        try:
            client.remove_object(bucket, object_key)
            return True
        except Exception as e:
            logger.warning(f"Failed to delete object '{object_key}' from MinIO: {e}")
            return False

    @staticmethod
    def file_exists(object_key: str, bucket_name: Optional[str] = None) -> bool:
        """Check if an object exists in MinIO."""
        bucket = bucket_name or settings.MINIO_BUCKET
        client = get_storage_client()
        try:
            client.stat_object(bucket, object_key)
            return True
        except Exception:
            return False

