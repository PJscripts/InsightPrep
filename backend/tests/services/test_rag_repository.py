"""Tests for SqlAlchemyKnowledgeRepository idempotency and persistence behavior."""

from unittest.mock import MagicMock

from app.services.rag.document_loader import compute_content_hash
from app.services.rag.ingestion_types import (
    IngestedChunk,
    IngestedDocument,
    ParsedDocument,
)
from app.services.rag.sqlalchemy_repository import SqlAlchemyKnowledgeRepository


def test_repository_get_document_hash_queries_database():
    mock_session = MagicMock()
    mock_session.scalar.return_value = "existing_sha256_hash"

    mock_factory = MagicMock()
    mock_factory.return_value.__enter__.return_value = mock_session

    repo = SqlAlchemyKnowledgeRepository(session_factory=mock_factory)
    h = repo.get_document_hash("dsa_arrays")

    assert h == "existing_sha256_hash"
    assert mock_session.scalar.called


def test_repository_atomicity_rolls_back_on_failure():
    mock_session = MagicMock()
    mock_session.scalar.return_value = None
    mock_session.flush.side_effect = RuntimeError("Database write error")

    mock_factory = MagicMock()
    mock_factory.return_value.__enter__.return_value = mock_session

    repo = SqlAlchemyKnowledgeRepository(session_factory=mock_factory)

    doc = ParsedDocument(
        source_key="atomic_test",
        title="Atomic Test",
        topic="dsa",
        source_origin="InsightPrep",
        source_license="project-authored",
        source_path="docs/test.md",
        content_hash="abc" * 21 + "a",
        body="Text body",
    )
    chunk = IngestedChunk(
        chunk_index=0,
        chunk_text="Text body",
        content_hash=compute_content_hash("Text body"),
    )
    ingested = IngestedDocument(document=doc, chunks=[chunk])

    try:
        repo.persist_document(ingested)
    except RuntimeError:
        pass

    assert mock_session.rollback.called
    assert not mock_session.commit.called


def test_repository_delete_document_returns_false_when_missing():
    mock_session = MagicMock()
    mock_session.scalar.return_value = None

    mock_factory = MagicMock()
    mock_factory.return_value.__enter__.return_value = mock_session

    repo = SqlAlchemyKnowledgeRepository(session_factory=mock_factory)
    res = repo.delete_document("non_existent_key")
    assert res is False
    assert not mock_session.commit.called
