"""dispatch

Revision ID: 6269073b6b0b
Revises: a9215bb6a3d1
Create Date: 2026-04-12 20:51:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '6269073b6b0b'
down_revision: Union[str, Sequence[str], None] = 'a9215bb6a3d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'dispatch',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted', sa.Boolean(), nullable=False),
        sa.Column('execution_id', sa.Uuid(), nullable=False),
        sa.Column('worker_response', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(['execution_id'], ['execution.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('dispatch')
