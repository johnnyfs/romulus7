"""execution metadata

Revision ID: a3c1d8e5f901
Revises: 5e8b7f4b96c2
Create Date: 2026-04-13 11:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a3c1d8e5f901"
down_revision: Union[str, Sequence[str], None] = "5e8b7f4b96c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "execution",
        sa.Column("metadata", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("execution", "metadata")
