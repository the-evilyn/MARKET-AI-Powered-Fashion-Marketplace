import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.cart.enums import CartStatus
from app.modules.catalog.models import ProductVariant
from app.modules.users.models import User


class Cart(Base):
    """Customer shopping cart entity."""

    __tablename__ = "carts"
    __table_args__ = (
        Index(
            "uq_carts_active_customer",
            "customer_id",
            unique=True,
            postgresql_where=text("status = 'ACTIVE'"),
            sqlite_where=text("status = 'ACTIVE'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[CartStatus] = mapped_column(
        SAEnum(
            CartStatus,
            name="cart_status",
            native_enum=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=CartStatus.ACTIVE,
        nullable=False,
        index=True,
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
    customer: Mapped[User] = relationship(
        User,
        lazy="selectin",
    )
    items: Mapped[List["CartItem"]] = relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="CartItem.created_at.asc()",
    )

    @property
    def subtotal(self) -> Decimal:
        """Deterministic sum of all item line totals using Decimal arithmetic."""
        return sum((item.line_total for item in self.items), Decimal("0.00"))

    @property
    def item_count(self) -> int:
        """Total number of physical units across all cart items."""
        return sum((item.quantity for item in self.items), 0)

    def __repr__(self) -> str:
        return f"<Cart id={self.id} customer_id={self.customer_id} status={self.status}>"


class CartItem(Base):
    """Individual SKU item within an active shopping cart."""

    __tablename__ = "cart_items"
    __table_args__ = (
        CheckConstraint("quantity >= 1", name="ck_cart_items_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_cart_items_unit_price_non_negative"),
        UniqueConstraint("cart_id", "variant_id", name="uq_cart_items_cart_variant"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    cart_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("carts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
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
    cart: Mapped[Cart] = relationship(
        Cart,
        back_populates="items",
    )
    variant: Mapped[ProductVariant] = relationship(
        ProductVariant,
        lazy="selectin",
    )

    @property
    def line_total(self) -> Decimal:
        """Deterministic line total using Decimal arithmetic (unit_price * quantity)."""
        return Decimal(str(self.unit_price)) * Decimal(str(self.quantity))

    @property
    def product_id(self) -> Optional[uuid.UUID]:
        return self.variant.product_id if self.variant else None

    @property
    def product_name(self) -> Optional[str]:
        return self.variant.product.name if self.variant and self.variant.product else None

    @property
    def sku(self) -> Optional[str]:
        return self.variant.sku if self.variant else None

    @property
    def color(self) -> Optional[str]:
        return self.variant.color if self.variant else None

    @property
    def size(self) -> Optional[str]:
        return self.variant.size if self.variant else None

    @property
    def is_in_stock(self) -> bool:
        return self.variant.is_in_stock if self.variant else False

    def __repr__(self) -> str:
        return f"<CartItem id={self.id} cart_id={self.cart_id} variant_id={self.variant_id} qty={self.quantity}>"
