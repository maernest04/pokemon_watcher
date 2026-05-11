"""add_language_to_search_query

Revision ID: a1c4d9b2e7f3
Revises: 7e6b481f996b
Create Date: 2026-05-11 11:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1c4d9b2e7f3'
down_revision: Union[str, Sequence[str], None] = '7e6b481f996b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('search_queries', schema=None) as batch_op:
        batch_op.add_column(sa.Column('language', sa.String(), nullable=False, server_default='english'))


def downgrade() -> None:
    with op.batch_alter_table('search_queries', schema=None) as batch_op:
        batch_op.drop_column('language')
