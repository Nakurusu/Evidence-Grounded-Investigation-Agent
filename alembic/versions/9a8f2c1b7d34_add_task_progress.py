"""add task progress fields

Revision ID: 9a8f2c1b7d34
Revises: e45b21784bee
Create Date: 2026-08-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "9a8f2c1b7d34"
down_revision: Union[str, Sequence[str], None] = "e45b21784bee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("tasks", sa.Column("current_stage", sa.String(), nullable=True))
    op.add_column(
        "tasks",
        sa.Column("progress", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("tasks", "progress")
    op.drop_column("tasks", "current_stage")
