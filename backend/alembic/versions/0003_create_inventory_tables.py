"""create inventory tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-29 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "inventory_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("variant_id", sa.Uuid(), nullable=False),
        sa.Column(
            "quantity_on_hand",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "quantity_reserved",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "low_stock_threshold",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("5"),
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
            ["variant_id"],
            ["product_variants.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("variant_id", name="uq_inventory_items_variant_id"),
        sa.CheckConstraint(
            "quantity_on_hand >= 0",
            name="ck_inventory_items_on_hand_non_negative",
        ),
        sa.CheckConstraint(
            "quantity_reserved >= 0",
            name="ck_inventory_items_reserved_non_negative",
        ),
        sa.CheckConstraint(
            "quantity_on_hand >= quantity_reserved",
            name="ck_inventory_items_on_hand_ge_reserved",
        ),
        sa.CheckConstraint(
            "low_stock_threshold >= 0",
            name="ck_inventory_items_threshold_non_negative",
        ),
    )
    op.create_index(
        op.f("ix_inventory_items_variant_id"),
        "inventory_items",
        ["variant_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_inventory_items_variant_id"), table_name="inventory_items")
    op.drop_table("inventory_items")
