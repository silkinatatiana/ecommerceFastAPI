"""Merge heads 20260111_tg_id_bigint and 7916f92361fa

Revision ID: 20260111_merge_heads
Revises: 20260111_tg_id_bigint, 7916f92361fa
Create Date: 2026-01-11
"""

# revision identifiers, used by Alembic.
revision = "20260111_merge_heads"
down_revision = ("20260111_tg_id_bigint", "7916f92361fa")
branch_labels = None
depends_on = None


def upgrade():
    # No-op merge migration
    pass


def downgrade():
    # No-op merge migration
    pass
