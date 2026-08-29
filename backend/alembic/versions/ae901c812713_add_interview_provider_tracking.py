"""add interview provider tracking

Revision ID: ae901c812713
Revises: bfddb49ee7e7
Create Date: 2026-08-29 13:49:38.508054

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ae901c812713"
down_revision: Union[str, Sequence[str], None] = "bfddb49ee7e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add provider tracking columns to interview sessions."""
    op.add_column(
        "interview_sessions",
        sa.Column(
            "question_provider",
            sa.String(length=20),
            server_default="gemini",
            nullable=False,
        ),
    )

    op.add_column(
        "interview_sessions",
        sa.Column(
            "evaluation_provider",
            sa.String(length=20),
            server_default="gemini",
            nullable=False,
        ),
    )

    op.alter_column(
        "interview_sessions",
        "question_provider",
        server_default=None,
    )

    op.alter_column(
        "interview_sessions",
        "evaluation_provider",
        server_default=None,
    )


def downgrade() -> None:
    """Remove provider tracking columns from interview sessions."""
    op.drop_column(
        "interview_sessions",
        "evaluation_provider",
    )

    op.drop_column(
        "interview_sessions",
        "question_provider",
    )
