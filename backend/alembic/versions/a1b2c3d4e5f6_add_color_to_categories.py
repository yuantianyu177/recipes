"""add color to tag and ingredient categories

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-02-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tag_categories', sa.Column('color', sa.String(7), nullable=True))
    op.add_column('ingredient_categories', sa.Column('color', sa.String(7), nullable=True))


def downgrade() -> None:
    op.drop_column('ingredient_categories', 'color')
    op.drop_column('tag_categories', 'color')
