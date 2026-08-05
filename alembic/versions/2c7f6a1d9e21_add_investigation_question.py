"""add investigation question to tasks

Revision ID: 2c7f6a1d9e21
Revises: 9a8f2c1b7d34
Create Date: 2026-08-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2c7f6a1d9e21"
down_revision: Union[str, Sequence[str], None] = "9a8f2c1b7d34"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("tasks", sa.Column("investigation_question", sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("tasks", "investigation_question")
