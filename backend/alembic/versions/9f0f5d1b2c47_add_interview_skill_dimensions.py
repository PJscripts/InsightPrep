"""add interview answer skill dimensions

Revision ID: 9f0f5d1b2c47
Revises: 9d3a5c7e4b21
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "9f0f5d1b2c47"
down_revision: Union[str, Sequence[str], None] = "9d3a5c7e4b21"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "interview_answers",
        sa.Column("skill_dimensions", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("interview_answers", "skill_dimensions")
