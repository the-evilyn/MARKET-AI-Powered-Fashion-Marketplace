"""create stores table

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-08 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stores",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("seller_id", sa.Uuid(), nullable=False),
        sa.Column("store_name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("logo_object_key", sa.String(length=255), nullable=True),
        sa.Column("banner_url", sa.String(length=500), nullable=True),
        sa.Column("banner_object_key", sa.String(length=255), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("contact_phone", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
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
            ["seller_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("seller_id", name="uq_stores_seller_id"),
        sa.UniqueConstraint("store_name", name="uq_stores_store_name"),
        sa.UniqueConstraint("slug", name="uq_stores_slug"),
    )
    op.create_index("ix_stores_seller_id", "stores", ["seller_id"])
    op.create_index("ix_stores_store_name", "stores", ["store_name"])
    op.create_index("ix_stores_slug", "stores", ["slug"])
    op.create_index("ix_stores_status", "stores", ["status"])


def downgrade() -> None:
    op.drop_index("ix_stores_status", table_name="stores")
    op.drop_index("ix_stores_slug", table_name="stores")
    op.drop_index("ix_stores_store_name", table_name="stores")
    op.drop_index("ix_stores_seller_id", table_name="stores")
    op.drop_table("stores")
