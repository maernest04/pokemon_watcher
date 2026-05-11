"""add_check_interval_and_restore_grading

Revision ID: 7e6b481f996b
Revises: 
Create Date: 2026-05-10 15:45:05.493932

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7e6b481f996b'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('search_queries', schema=None) as batch_op:
        batch_op.add_column(sa.Column('check_interval_mins', sa.Integer(), nullable=False, server_default='5'))
        batch_op.add_column(sa.Column('last_polled_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('search_queries', schema=None) as batch_op:
        batch_op.drop_column('last_polled_at')
        batch_op.drop_column('check_interval_mins')
