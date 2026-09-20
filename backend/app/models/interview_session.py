from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    resume_id: Mapped[int | None] = mapped_column(
        ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    interview_mode: Mapped[str] = mapped_column(
        String(20),
        default="fixed",
        nullable=False,
    )

    interview_type: Mapped[str] = mapped_column(
        String(30),
        default="technical",
    )

    difficulty: Mapped[str] = mapped_column(
        String(20),
        default="medium",
    )

    total_questions: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=10,
    )

    current_question: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="created",
    )

    current_topic: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    topic_question_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    covered_topics: Mapped[list[Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    question_provider: Mapped[str] = mapped_column(
        String(20),
        default="gemini",
        nullable=False,
    )

    evaluation_provider: Mapped[str] = mapped_column(
        String(20),
        default="gemini",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    user = relationship(
        "User",
        back_populates="interview_sessions",
    )

    resume = relationship(
        "Resume",
    )

    questions = relationship(
        "InterviewQuestion",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="InterviewQuestion.question_number",
    )
