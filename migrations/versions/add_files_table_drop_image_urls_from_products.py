"""add files table and drop image_urls from products

Revision ID: add_files_image_urls
Revises: ced85fc95835
Create Date: 2026-03-07

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "ced85fc95835"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create files table
    op.create_table(
        "files",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(), nullable=False),
        sa.Column("s3_key", sa.String(), nullable=False),
        sa.Column("file_url", sa.String(), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), nullable=True),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_files_id"), "files", ["id"], unique=False)
    op.create_index(op.f("ix_files_s3_key"), "files", ["s3_key"], unique=True)

    # Drop image_urls from products
    op.drop_column("products", "image_urls")


def downgrade() -> None:
    """Downgrade schema."""
    # Restore image_urls to products
    op.add_column(
        "products",
        sa.Column("image_urls", sa.JSON(), nullable=True),
    )

    # Drop files table
    op.drop_index(op.f("ix_files_s3_key"), table_name="files")
    op.drop_index(op.f("ix_files_id"), table_name="files")
    op.drop_table("files")
