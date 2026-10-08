import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Text, Uuid, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref

from app.core.database import Base
from app.modules.seller.enums import StoreStatus

if TYPE_CHECKING:
    from app.modules.users.models import User


class Store(Base):
    """Store entity representing a public multi-vendor storefront."""

    __tablename__ = "stores"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
        index=True,
    )
    store_name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    slug: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        nullable=False,
        index=True,
    )
    bio: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    logo_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    logo_object_key: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    banner_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    banner_object_key: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    contact_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    contact_phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    status: Mapped[StoreStatus] = mapped_column(
        SAEnum(
            StoreStatus,
            name="store_status",
            native_enum=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=StoreStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User",
        backref=backref("store", uselist=False),
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<Store id={self.id} name={self.store_name} slug={self.slug} status={self.status}>"
