from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    question_id: Mapped[int] = mapped_column(
        ForeignKey("interview_questions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    answer_text: Mapped[str] = mapped_column(Text, nullable=False)

    score: Mapped[float | None] = mapped_column(Float, nullable=True)

    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    skill_dimensions: Mapped[dict[str, float] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    question = relationship("InterviewQuestion", back_populates="answer")
