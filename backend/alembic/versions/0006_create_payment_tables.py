"""create payment tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-30 15:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Payments table
    op.create_table(
        "payments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False, server_default="PAYPAL"),
        sa.Column("provider_order_id", sa.String(length=128), nullable=True),
        sa.Column("provider_payment_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id", name="uq_payments_order_id"),
        sa.CheckConstraint("amount >= 0", name="ck_payments_amount_non_negative"),
    )
    op.create_index(op.f("ix_payments_order_id"), "payments", ["order_id"], unique=True)
    op.create_index(op.f("ix_payments_provider_order_id"), "payments", ["provider_order_id"], unique=False)
    op.create_index(op.f("ix_payments_provider_payment_id"), "payments", ["provider_payment_id"], unique=False)
    op.create_index(op.f("ix_payments_status"), "payments", ["status"], unique=False)

    # 2. Payment Webhook Events table (Idempotency)
    op.create_table(
        "payment_webhook_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("event_id", sa.String(length=128), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "event_id", name="uq_payment_webhook_events_provider_event_id"),
    )
    op.create_index(op.f("ix_payment_webhook_events_provider"), "payment_webhook_events", ["provider"], unique=False)
    op.create_index(op.f("ix_payment_webhook_events_event_id"), "payment_webhook_events", ["event_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_payment_webhook_events_event_id"), table_name="payment_webhook_events")
    op.drop_index(op.f("ix_payment_webhook_events_provider"), table_name="payment_webhook_events")
    op.drop_table("payment_webhook_events")

    op.drop_index(op.f("ix_payments_status"), table_name="payments")
    op.drop_index(op.f("ix_payments_provider_payment_id"), table_name="payments")
    op.drop_index(op.f("ix_payments_provider_order_id"), table_name="payments")
    op.drop_index(op.f("ix_payments_order_id"), table_name="payments")
    op.drop_table("payments")
