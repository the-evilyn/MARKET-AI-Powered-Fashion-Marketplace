from datetime import datetime, timezone
from typing import Dict, Optional
from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """General service health status."""
    status: str = Field(default="ok", description="Overall service status")
    app_name: str = Field(description="Name of the application")
    version: str = Field(description="Semantic version")
    environment: str = Field(description="Deployment environment")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReadinessResponse(BaseModel):
    """Infrastructure dependencies readiness status."""
    status: str = Field(description="Overall readiness: 'ready' or 'not_ready'")
    components: Dict[str, str] = Field(description="Health status of individual backing services")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LivenessResponse(BaseModel):
    """Container liveness status."""
    status: str = Field(default="alive", description="Process liveness check")
