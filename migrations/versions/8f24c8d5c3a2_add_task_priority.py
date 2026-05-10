"""add task priority

Revision ID: 8f24c8d5c3a2
Revises: b4f789f4f307
Create Date: 2026-05-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8f24c8d5c3a2"
down_revision: Union[str, Sequence[str], None] = "b4f789f4f307"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "tasks",
        sa.Column(
            "priority",
            sa.String(),
            nullable=False,
            server_default="medium",
        ),
    )
    op.alter_column("tasks", "priority", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("tasks", "priority")
