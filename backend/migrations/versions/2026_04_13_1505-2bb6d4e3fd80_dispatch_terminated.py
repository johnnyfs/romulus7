"""dispatch terminated

Revision ID: 2bb6d4e3fd80
Revises: 3e8ad4d27076
Create Date: 2026-04-13 15:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2bb6d4e3fd80'
down_revision: Union[str, Sequence[str], None] = '3e8ad4d27076'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'dispatch',
        sa.Column('terminated', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column('dispatch', 'terminated', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('dispatch', 'terminated')
