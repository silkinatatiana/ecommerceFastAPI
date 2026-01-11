"""Make tg_id BigInteger

Revision ID: 20260111_tg_id_bigint
Revises: eb7ec3aa93c5
Create Date: 2026-01-11
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260111_tg_id_bigint"
down_revision = "eb7ec3aa93c5"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "users",
        "tg_id",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=True,
    )


def downgrade():
    op.alter_column(
        "users",
        "tg_id",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=True,
    )
