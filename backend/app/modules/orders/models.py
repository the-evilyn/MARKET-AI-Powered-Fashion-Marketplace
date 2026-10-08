from datetime import datetime, timezone
from decimal import Decimal
import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.catalog.models import ProductVariant
from app.modules.orders.enums import OrderStatus
from app.modules.users.models import User

if TYPE_CHECKING:
    from app.modules.payments.models import Payment


class Order(Base):
    """Customer purchase order entity."""

    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="ck_orders_subtotal_non_negative"),
        CheckConstraint("total >= 0", name="ck_orders_total_non_negative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    order_number: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(
            OrderStatus,
            name="order_status",
            native_enum=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=OrderStatus.PENDING_PAYMENT,
        nullable=False,
        index=True,
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
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
    customer: Mapped[User] = relationship(
        User,
        lazy="selectin",
    )
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="OrderItem.created_at.asc()",
    )
    sub_orders: Mapped[List["SubOrder"]] = relationship(
        "SubOrder",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="SubOrder.created_at.asc()",
    )
    payment: Mapped[Optional["Payment"]] = relationship(
        "Payment",
        back_populates="order",
        uselist=False,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Order id={self.id} order_number={self.order_number} status={self.status} total={self.total}>"


class SubOrder(Base):
    """Vendor-scoped fulfillment sub-order partition."""

    __tablename__ = "sub_orders"
    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="ck_sub_orders_subtotal_non_negative"),
        CheckConstraint("shipping_amount >= 0", name="ck_sub_orders_shipping_amount_non_negative"),
        CheckConstraint("total >= 0", name="ck_sub_orders_total_non_negative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    sub_order_number: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(
            OrderStatus,
            name="order_status",
            native_enum=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=OrderStatus.PENDING_PAYMENT,
        nullable=False,
        index=True,
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    shipping_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    carrier: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )
    tracking_number: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
    )
    shipped_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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
    order: Mapped[Order] = relationship(
        "Order",
        back_populates="sub_orders",
    )
    seller: Mapped[User] = relationship(
        User,
        foreign_keys=[seller_id],
        lazy="selectin",
    )
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="sub_order",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="OrderItem.created_at.asc()",
    )

    def __repr__(self) -> str:
        return f"<SubOrder id={self.id} number={self.sub_order_number} seller={self.seller_id} status={self.status}>"


class OrderItem(Base):
    """Historical line item snapshot captured at checkout time."""

    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity >= 1", name="ck_order_items_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_order_items_unit_price_non_negative"),
        CheckConstraint("line_total >= 0", name="ck_order_items_line_total_non_negative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sub_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("sub_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    seller_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    variant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    product_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    sku: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    order: Mapped[Order] = relationship(
        Order,
        back_populates="items",
    )
    sub_order: Mapped[Optional[SubOrder]] = relationship(
        SubOrder,
        back_populates="items",
    )
    seller: Mapped[Optional[User]] = relationship(
        User,
        foreign_keys=[seller_id],
        lazy="selectin",
    )
    variant: Mapped[Optional[ProductVariant]] = relationship(
        ProductVariant,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<OrderItem id={self.id} order_id={self.order_id} sku={self.sku} qty={self.quantity} total={self.line_total}>"

