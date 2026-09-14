"""add interview question uniqueness

Revision ID: 0cd622f9fea4
Revises: ae901c812713
Create Date: 2026-09-13 12:09:15.467830

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0cd622f9fea4"
down_revision: Union[str, Sequence[str], None] = "ae901c812713"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_interview_questions_session_number",
        "interview_questions",
        ["session_id", "question_number"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_interview_questions_session_number",
        "interview_questions",
        type_="unique",
    )
