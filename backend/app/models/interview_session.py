from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
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

    interview_type: Mapped[str] = mapped_column(
        String(30),
        default="technical",
    )

    difficulty: Mapped[str] = mapped_column(
        String(20),
        default="medium",
    )

    total_questions: Mapped[int] = mapped_column(
        Integer,
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
