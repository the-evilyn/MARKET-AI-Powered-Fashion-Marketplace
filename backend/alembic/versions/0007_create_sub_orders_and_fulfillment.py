"""create sub_orders table and multi-vendor fulfillment columns

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-07 23:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create sub_orders table
    op.create_table(
        "sub_orders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("seller_id", sa.Uuid(), nullable=False),
        sa.Column("sub_order_number", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING_PAYMENT"),
        sa.Column("subtotal", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("shipping_amount", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"),
        sa.Column("total", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("carrier", sa.String(length=64), nullable=True),
        sa.Column("tracking_number", sa.String(length=128), nullable=True),
        sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["seller_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("subtotal >= 0", name="ck_sub_orders_subtotal_non_negative"),
        sa.CheckConstraint("shipping_amount >= 0", name="ck_sub_orders_shipping_amount_non_negative"),
        sa.CheckConstraint("total >= 0", name="ck_sub_orders_total_non_negative"),
    )
    op.create_index(op.f("ix_sub_orders_order_id"), "sub_orders", ["order_id"], unique=False)
    op.create_index(op.f("ix_sub_orders_seller_id"), "sub_orders", ["seller_id"], unique=False)
    op.create_index(op.f("ix_sub_orders_sub_order_number"), "sub_orders", ["sub_order_number"], unique=True)
    op.create_index(op.f("ix_sub_orders_status"), "sub_orders", ["status"], unique=False)

    # 2. Add columns to order_items
    op.add_column("order_items", sa.Column("sub_order_id", sa.Uuid(), nullable=True))
    op.add_column("order_items", sa.Column("seller_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_order_items_sub_order_id",
        "order_items",
        "sub_orders",
        ["sub_order_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_order_items_seller_id",
        "order_items",
        "users.id" if False else "users",
        ["seller_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(op.f("ix_order_items_sub_order_id"), "order_items", ["sub_order_id"], unique=False)
    op.create_index(op.f("ix_order_items_seller_id"), "order_items", ["seller_id"], unique=False)

    # 3. Add metadata columns to product_media
    op.add_column("product_media", sa.Column("file_size", sa.Integer(), nullable=True))
    op.add_column("product_media", sa.Column("mime_type", sa.String(length=64), nullable=True))
    op.add_column("product_media", sa.Column("original_filename", sa.String(length=255), nullable=True))


def downgrade() -> None:
    # Remove product_media columns
    op.drop_column("product_media", "original_filename")
    op.drop_column("product_media", "mime_type")
    op.drop_column("product_media", "file_size")

    # Remove order_items columns and constraints
    op.drop_index(op.f("ix_order_items_seller_id"), table_name="order_items")
    op.drop_index(op.f("ix_order_items_sub_order_id"), table_name="order_items")
    op.drop_constraint("fk_order_items_seller_id", "order_items", type_="foreignkey")
    op.drop_constraint("fk_order_items_sub_order_id", "order_items", type_="foreignkey")
    op.drop_column("order_items", "seller_id")
    op.drop_column("order_items", "sub_order_id")

    # Drop sub_orders table
    op.drop_index(op.f("ix_sub_orders_status"), table_name="sub_orders")
    op.drop_index(op.f("ix_sub_orders_sub_order_number"), table_name="sub_orders")
    op.drop_index(op.f("ix_sub_orders_seller_id"), table_name="sub_orders")
    op.drop_index(op.f("ix_sub_orders_order_id"), table_name="sub_orders")
    op.drop_table("sub_orders")
