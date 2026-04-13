"""sandbox worker lease execution

Revision ID: a9215bb6a3d1
Revises: 42a0d3bc2cdb
Create Date: 2026-04-12 19:28:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'a9215bb6a3d1'
down_revision: Union[str, Sequence[str], None] = '42a0d3bc2cdb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'sandbox',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted', sa.Boolean(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'execution',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted', sa.Boolean(), nullable=False),
        sa.Column('spec', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'worker_lease',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted', sa.Boolean(), nullable=False),
        sa.Column('worker_id', sa.Uuid(), nullable=False),
        sa.Column('sandbox_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['sandbox_id'], ['sandbox.id'], ),
        sa.ForeignKeyConstraint(['worker_id'], ['worker.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        'unique_worker_lease_worker_id_sandbox_id_not_deleted',
        'worker_lease',
        ['worker_id', 'sandbox_id'],
        unique=True,
        postgresql_where=sa.text('deleted IS FALSE')
    )
    op.create_index(
        'unique_worker_lease_sandbox_id_not_deleted',
        'worker_lease',
        ['sandbox_id'],
        unique=True,
        postgresql_where=sa.text('deleted IS FALSE')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('unique_worker_lease_sandbox_id_not_deleted', table_name='worker_lease', postgresql_where=sa.text('deleted IS FALSE'))
    op.drop_index('unique_worker_lease_worker_id_sandbox_id_not_deleted', table_name='worker_lease', postgresql_where=sa.text('deleted IS FALSE'))
    op.drop_table('worker_lease')
    op.drop_table('execution')
    op.drop_table('sandbox')
