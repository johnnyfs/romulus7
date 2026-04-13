"""event

Revision ID: 0f85a2d4a7d1
Revises: 6269073b6b0b
Create Date: 2026-04-12 22:37:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0f85a2d4a7d1'
down_revision: Union[str, Sequence[str], None] = '6269073b6b0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'event',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source_type', sa.String(), nullable=False),
        sa.Column('source_id', sa.Uuid(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        'ix_event_source_type_source_id_id',
        'event',
        ['source_type', 'source_id', 'id'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_event_source_type_source_id_id', table_name='event')
    op.drop_table('event')
