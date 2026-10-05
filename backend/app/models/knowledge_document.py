"""Curated knowledge-source metadata for RAG retrieval."""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[int] = mapped_column(primary_key=True)

    source_key: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)

    topic: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    source_origin: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    source_license: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="project-authored",
    )

    source_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    content_hash: Mapped[str] = mapped_column(
        String(64),
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

    chunks = relationship(
        "KnowledgeChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )
