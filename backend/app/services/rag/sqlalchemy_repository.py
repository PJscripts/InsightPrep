"""SQLAlchemy-backed implementation of KnowledgePersistenceRepository."""

import logging
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import KnowledgeDocument
from app.services.rag.ingestion_types import IngestedDocument
from app.services.rag.repository_interface import KnowledgePersistenceRepository

logger = logging.getLogger(__name__)


class SqlAlchemyKnowledgeRepository(KnowledgePersistenceRepository):
    """Persists RAG documents and chunks atomically using SQLAlchemy."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self.session_factory = session_factory

    def get_document_hash(self, source_key: str) -> str | None:
        """Fetch the existing content_hash for source_key, or None if not found."""
        with self.session_factory() as session:
            stmt = select(KnowledgeDocument.content_hash).where(
                KnowledgeDocument.source_key == source_key
            )
            return session.scalar(stmt)

    def persist_document(self, ingested_document: IngestedDocument) -> None:
        """Persist or atomically replace an ingested document and its chunks."""
        parsed = ingested_document.document
        with self.session_factory() as session:
            try:
                # Query existing document
                stmt = select(KnowledgeDocument).where(
                    KnowledgeDocument.source_key == parsed.source_key
                )
                doc = session.scalar(stmt)

                if doc is None:
                    # New document insertion
                    doc = KnowledgeDocument(
                        source_key=parsed.source_key,
                        title=parsed.title,
                        topic=parsed.topic,
                        source_origin=parsed.source_origin,
                        source_license=parsed.source_license,
                        source_path=parsed.source_path,
                        content_hash=parsed.content_hash,
                    )
                    session.add(doc)
                    session.flush()  # populate doc.id for chunk FK
                else:
                    # Update metadata and content_hash
                    doc.title = parsed.title
                    doc.topic = parsed.topic
                    doc.source_origin = parsed.source_origin
                    doc.source_license = parsed.source_license
                    doc.source_path = parsed.source_path
                    doc.content_hash = parsed.content_hash

                    # Remove existing chunks cleanly (relies on relationship or flush)
                    doc.chunks.clear()
                    session.flush()

                # Add new chunks
                for chunk in ingested_document.chunks:
                    chunk_row = KnowledgeChunk(
                        document_id=doc.id,
                        chunk_index=chunk.chunk_index,
                        chunk_text=chunk.chunk_text,
                        content_hash=chunk.content_hash,
                        embedding=list(chunk.embedding)
                        if chunk.embedding is not None
                        else None,
                    )
                    session.add(chunk_row)

                session.commit()
                logger.info(
                    "Persisted document %s with %d chunks.",
                    parsed.source_key,
                    ingested_document.chunk_count,
                )
            except Exception:
                session.rollback()
                logger.exception(
                    "Transaction rolled back while persisting document %s",
                    parsed.source_key,
                )
                raise

    def delete_document(self, source_key: str) -> bool:
        """Remove a document and its cascaded chunks by source_key."""
        with self.session_factory() as session:
            try:
                stmt = select(KnowledgeDocument).where(
                    KnowledgeDocument.source_key == source_key
                )
                doc = session.scalar(stmt)
                if doc is None:
                    return False

                session.delete(doc)
                session.commit()
                return True
            except Exception:
                session.rollback()
                logger.exception("Failed to delete document %s", source_key)
                raise
