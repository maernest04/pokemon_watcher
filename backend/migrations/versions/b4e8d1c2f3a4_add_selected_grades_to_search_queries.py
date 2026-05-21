"""add selected_grades to search_queries

Revision ID: b4e8d1c2f3a4
Revises: 9d2f457b49d3
Create Date: 2026-05-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b4e8d1c2f3a4'
down_revision: Union[str, Sequence[str], None] = '9d2f457b49d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('search_queries', sa.Column('selected_grades', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('search_queries', 'selected_grades')
