from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    resumes = relationship(
        "Resume",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    interview_sessions = relationship(
        "InterviewSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )
