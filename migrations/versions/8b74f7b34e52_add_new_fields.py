"""add new fields

Revision ID: 8b74f7b34e52
Revises: 2880650da84f
Create Date: 2025-07-15 15:38:23.153534

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b74f7b34e52'
down_revision: Union[str, None] = '2880650da84f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('products', sa.Column('RAM_capacity', sa.String()))
    op.add_column('products', sa.Column('built_in_memory_capacity', sa.String()))
    op.add_column('products', sa.Column('screen', sa.Float()))
    op.add_column('products', sa.Column('CPU', sa.String()))
    op.add_column('products', sa.Column('number_of_processor_cores', sa.Integer()))
    op.add_column('products', sa.Column('number_of_graphics_cores', sa.Integer()))
    op.add_column('products', sa.Column('color', sa.String()))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('products', 'RAM_capacity')
    op.drop_column('products', 'built_in_memory_capacity')
    op.drop_column('products', 'screen')
    op.drop_column('products', 'CPU')
    op.drop_column('products', 'number_of_processor_cores')
    op.drop_column('products', 'number_of_graphics_cores')
    op.drop_column('products', 'color')
