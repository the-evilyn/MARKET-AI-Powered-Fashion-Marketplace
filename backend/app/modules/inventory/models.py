import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.modules.catalog.models import ProductVariant


class InventoryItem(Base):
    """Real-time inventory tracking at the SKU/variant level."""

    __tablename__ = "inventory_items"
    __table_args__ = (
        CheckConstraint(
            "quantity_on_hand >= 0",
            name="ck_inventory_items_on_hand_non_negative",
        ),
        CheckConstraint(
            "quantity_reserved >= 0",
            name="ck_inventory_items_reserved_non_negative",
        ),
        CheckConstraint(
            "quantity_on_hand >= quantity_reserved",
            name="ck_inventory_items_on_hand_ge_reserved",
        ),
        CheckConstraint(
            "low_stock_threshold >= 0",
            name="ck_inventory_items_threshold_non_negative",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    quantity_on_hand: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    quantity_reserved: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    low_stock_threshold: Mapped[int] = mapped_column(
        Integer,
        default=5,
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

    # Relationships
    variant: Mapped["ProductVariant"] = relationship(
        "ProductVariant",
        back_populates="inventory",
    )

    # Computed Properties
    @property
    def quantity_available(self) -> int:
        """Physical units available for sale (on hand minus reserved)."""
        return max(0, self.quantity_on_hand - self.quantity_reserved)

    @property
    def is_in_stock(self) -> bool:
        """Whether at least one purchasable unit is currently available."""
        return self.quantity_available > 0

    @property
    def is_low_stock(self) -> bool:
        """Whether current available stock has reached or dropped below the threshold."""
        return self.quantity_available <= self.low_stock_threshold

    def __repr__(self) -> str:
        return (
            f"<InventoryItem id={self.id} variant_id={self.variant_id} "
            f"on_hand={self.quantity_on_hand} reserved={self.quantity_reserved} "
            f"available={self.quantity_available}>"
        )
