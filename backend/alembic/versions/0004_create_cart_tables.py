"""create cart tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-29 23:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Carts table
    op.create_table(
        "carts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="ACTIVE",
        ),
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
            ["customer_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_carts_customer_id"), "carts", ["customer_id"], unique=False)
    op.create_index(op.f("ix_carts_status"), "carts", ["status"], unique=False)
    op.create_index(
        "uq_carts_active_customer",
        "carts",
        ["customer_id"],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE'"),
        sqlite_where=sa.text("status = 'ACTIVE'"),
    )

    # 2. Cart Items table
    op.create_table(
        "cart_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("cart_id", sa.Uuid(), nullable=False),
        sa.Column("variant_id", sa.Uuid(), nullable=False),
        sa.Column(
            "quantity",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column(
            "unit_price",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
        ),
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
            ["cart_id"],
            ["carts.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["variant_id"],
            ["product_variants.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cart_id", "variant_id", name="uq_cart_items_cart_variant"),
        sa.CheckConstraint("quantity >= 1", name="ck_cart_items_quantity_positive"),
        sa.CheckConstraint("unit_price >= 0", name="ck_cart_items_unit_price_non_negative"),
    )
    op.create_index(op.f("ix_cart_items_cart_id"), "cart_items", ["cart_id"], unique=False)
    op.create_index(op.f("ix_cart_items_variant_id"), "cart_items", ["variant_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_cart_items_variant_id"), table_name="cart_items")
    op.drop_index(op.f("ix_cart_items_cart_id"), table_name="cart_items")
    op.drop_table("cart_items")

    op.drop_index("uq_carts_active_customer", table_name="carts")
    op.drop_index(op.f("ix_carts_status"), table_name="carts")
    op.drop_index(op.f("ix_carts_customer_id"), table_name="carts")
    op.drop_table("carts")
