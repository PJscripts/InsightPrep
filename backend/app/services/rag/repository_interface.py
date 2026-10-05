"""Abstract repository interface for RAG knowledge persistence."""

from typing import Protocol

from app.services.rag.ingestion_types import IngestedDocument


class KnowledgePersistenceRepository(Protocol):
    """Decoupled persistence interface for RAG documents and chunks.

    Implemented without touching the live database during Milestone 3.
    Concrete database persistence will be attached in a subsequent milestone
    once the pgvector container environment is safely ready.
    """

    def get_document_hash(self, source_key: str) -> str | None:
        """Fetch the existing content_hash for source_key, if present."""
        ...

    def persist_document(self, ingested_document: IngestedDocument) -> None:
        """Persist or upsert an ingested document and its chunks."""
        ...

    def delete_document(self, source_key: str) -> bool:
        """Remove a document and its cascaded chunks by source_key."""
        ...
