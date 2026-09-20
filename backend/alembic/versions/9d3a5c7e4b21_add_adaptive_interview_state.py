"""add adaptive interview state

Revision ID: 9d3a5c7e4b21
Revises: 0cd6229f9ea4
Create Date: 2026-09-14 12:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "9d3a5c7e4b21"
down_revision: Union[str, Sequence[str], None] = "0cd622f9fea4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "interview_sessions",
        sa.Column(
            "interview_mode",
            sa.String(length=20),
            server_default="fixed",
            nullable=False,
        ),
    )

    op.add_column(
        "interview_sessions",
        sa.Column(
            "current_topic",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.add_column(
        "interview_sessions",
        sa.Column(
            "topic_question_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )

    op.add_column(
        "interview_sessions",
        sa.Column(
            "covered_topics",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )

    op.alter_column(
        "interview_sessions",
        "total_questions",
        existing_type=sa.Integer(),
        nullable=True,
    )

    op.alter_column(
        "interview_sessions",
        "interview_mode",
        server_default=None,
    )

    op.alter_column(
        "interview_sessions",
        "topic_question_count",
        server_default=None,
    )


def downgrade() -> None:
    op.execute(
        "UPDATE interview_sessions "
        "SET total_questions = 0 "
        "WHERE total_questions IS NULL"
    )

    op.alter_column(
        "interview_sessions",
        "total_questions",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.drop_column("interview_sessions", "covered_topics")
    op.drop_column("interview_sessions", "topic_question_count")
    op.drop_column("interview_sessions", "current_topic")
    op.drop_column("interview_sessions", "interview_mode")
