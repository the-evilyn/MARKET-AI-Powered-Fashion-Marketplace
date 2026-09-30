from datetime import datetime, timezone
from decimal import Decimal
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.payments.enums import PaymentProvider, PaymentStatus

if TYPE_CHECKING:
    from app.modules.orders.models import Order


class Payment(Base):
    """Payment record linked to a customer order."""

    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_payments_amount_non_negative"),
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
        unique=True,
        index=True,
    )
    provider: Mapped[PaymentProvider] = mapped_column(
        SAEnum(
            PaymentProvider,
            name="payment_provider",
            native_enum=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=PaymentProvider.PAYPAL,
        nullable=False,
    )
    provider_order_id: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )
    provider_payment_id: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )
    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(
            PaymentStatus,
            name="payment_status",
            native_enum=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(
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
    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="payment",
    )

    def __repr__(self) -> str:
        return (
            f"<Payment id={self.id} order_id={self.order_id} provider={self.provider} "
            f"status={self.status} amount={self.amount} {self.currency}>"
        )


class PaymentWebhookEvent(Base):
    """Tracks received payment webhook events for idempotency."""

    __tablename__ = "payment_webhook_events"
    __table_args__ = (
        UniqueConstraint("provider", "event_id", name="uq_payment_webhook_events_provider_event_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    provider: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )
    event_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<PaymentWebhookEvent id={self.id} provider={self.provider} event_id={self.event_id}>"
