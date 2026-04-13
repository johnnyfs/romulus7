"""execution name

Revision ID: 5e8b7f4b96c2
Revises: 0f85a2d4a7d1
Create Date: 2026-04-13 10:15:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "5e8b7f4b96c2"
down_revision: Union[str, Sequence[str], None] = "0f85a2d4a7d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "execution",
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )
    op.execute(
        """
        UPDATE execution
        SET name = COALESCE(
            NULLIF(BTRIM(spec->>'command'), ''),
            'command'
        )
        WHERE name IS NULL
        """
    )
    op.alter_column("execution", "name", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("execution", "name")
