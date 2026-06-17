"""add task history

Revision ID: 9f0a1b2c3d4e
Revises: 4b7d3c9a2e11
Create Date: 2026-05-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9f0a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "4b7d3c9a2e11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "task_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("method", sa.String(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=True),
        sa.Column("task_title", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_task_history_id"), "task_history", ["id"], unique=False)
    op.create_index(op.f("ix_task_history_method"), "task_history", ["method"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_task_history_method"), table_name="task_history")
    op.drop_index(op.f("ix_task_history_id"), table_name="task_history")
    op.drop_table("task_history")
