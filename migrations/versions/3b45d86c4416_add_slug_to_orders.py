"""Add slug to orders

Revision ID: 3b45d86c4416
Revises: c468bda49966
Create Date: 2025-12-30 00:00:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "3b45d86c4416"
down_revision: str | None = "c468bda49966"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("orders", sa.Column("slug", sa.UUID(), nullable=True))

    # Populate existing rows with unique slugs to satisfy NOT NULL constraint.
    connection = op.get_bind()
    existing_orders = connection.execute(sa.text("SELECT id FROM orders")).fetchall()
    for row in existing_orders:
        connection.execute(
            sa.text("UPDATE orders SET slug = :slug WHERE id = :id"),
            {"slug": str(uuid.uuid4()), "id": row.id},
        )

    op.alter_column("orders", "slug", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("orders", "slug")
