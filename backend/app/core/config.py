import json
import logging
from functools import lru_cache
from typing import List, Optional, Union
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("ai_fashion_marketplace.config")

INSECURE_DEFAULT_JWT_SECRETS = {
    "super_secret_jwt_signing_key_replace_in_production_min32chars",
    "secret",
    "changeme",
    "jwt_secret",
    "your_jwt_secret",
    "replace_in_production",
    "password",
    "12345678",
    "secret123",
    "admin",
}



class Settings(BaseSettings):
    """Application settings and environment configurations."""

    # Application
    APP_ENV: str = "development"
    APP_NAME: str = "AI Fashion Marketplace"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # PostgreSQL + pgvector
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fashion_marketplace"

    # Redis Cache & State
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT Authentication (Settings foundation ready for Auth module)
    JWT_SECRET: str = "super_secret_jwt_signing_key_replace_in_production_min32chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    # MinIO / S3 Object Storage (Architecture-ready for AI media & assets)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "fashion-media"
    MINIO_USE_SSL: bool = False

    # PayPal Sandbox Configuration
    PAYPAL_CLIENT_ID: Optional[str] = None
    PAYPAL_CLIENT_SECRET: Optional[str] = None
    PAYPAL_BASE_URL: str = "https://api-m.sandbox.paypal.com"
    PAYPAL_WEBHOOK_ID: Optional[str] = None

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.strip().startswith("[") and v.strip().endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item) for item in parsed]
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            return [str(i) for i in v]
        return []

    @model_validator(mode="after")
    def validate_jwt_secret_safety(self) -> "Settings":
        env = (self.APP_ENV or "").strip().lower()
        secret = (self.JWT_SECRET or "").strip()

        # JWT Secret cannot be empty in any environment
        if not secret:
            raise ValueError("JWT signing key must not be empty.")

        if env in ("production", "prod", "staging"):
            # Enforce strong secret in production and staging
            if secret.lower() in INSECURE_DEFAULT_JWT_SECRETS:
                raise ValueError(
                    "Insecure default JWT signing key detected in production/staging environment. "
                    "A strong, unique signing key of at least 32 characters is required."
                )
            if len(secret) < 32:
                raise ValueError(
                    "JWT signing key must be at least 32 characters long in production/staging environment."
                )
        else:
            if secret.lower() in INSECURE_DEFAULT_JWT_SECRETS:
                logger.warning(
                    "Using default JWT signing key in non-production environment. "
                    "Ensure a strong, unique key is set for production and staging."
                )

        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
        hide_input_in_errors=True,
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
