"""Unit tests for VectorRetrievalService (database-independent)."""

from unittest.mock import MagicMock

from app.services.rag.retrieval_service import (
    VectorRetrievalService,
)
from app.services.rag.retrieval_types import RetrievalFailureCode, RetrievalStatus
from app.services.rag.types import EmbeddingFailureCode, EmbeddingResult


def test_empty_or_whitespace_query_returns_unavailable():
    mock_provider = MagicMock()
    mock_factory = MagicMock()

    service = VectorRetrievalService(
        session_factory=mock_factory,
        embedding_provider=mock_provider,
    )

    r1 = service.retrieve("")
    assert not r1.is_success
    assert r1.status == RetrievalStatus.UNAVAILABLE
    assert r1.failure_code == RetrievalFailureCode.INVALID_QUERY

    r2 = service.retrieve("   \t\n ")
    assert not r2.is_success
    assert r2.failure_code == RetrievalFailureCode.INVALID_QUERY

    r3 = service.retrieve(None)  # type: ignore
    assert not r3.is_success
    assert r3.failure_code == RetrievalFailureCode.INVALID_QUERY


def test_embedding_failure_returns_typed_unavailable():
    mock_provider = MagicMock()
    mock_provider.embed.return_value = EmbeddingResult.unavailable(
        failure_code=EmbeddingFailureCode.MODEL_LOAD_FAILED,
        detail="Model failed to load",
    )
    mock_factory = MagicMock()

    service = VectorRetrievalService(
        session_factory=mock_factory,
        embedding_provider=mock_provider,
    )

    res = service.retrieve("Explain B-Trees")
    assert not res.is_success
    assert res.status == RetrievalStatus.UNAVAILABLE
    assert res.failure_code == RetrievalFailureCode.EMBEDDING_FAILED
    assert "model_load_failed" in (res.detail or "").lower()
    assert not mock_factory.called


def test_database_exception_returns_typed_unavailable():
    mock_provider = MagicMock()
    mock_provider.embed.return_value = EmbeddingResult.available(tuple([0.05] * 384))

    mock_session = MagicMock()
    mock_session.execute.side_effect = RuntimeError("Database connection lost")

    mock_factory = MagicMock()
    mock_factory.return_value.__enter__.return_value = mock_session

    service = VectorRetrievalService(
        session_factory=mock_factory,
        embedding_provider=mock_provider,
    )

    res = service.retrieve("What is paging?")
    assert not res.is_success
    assert res.status == RetrievalStatus.UNAVAILABLE
    assert res.failure_code == RetrievalFailureCode.DATABASE_ERROR
    assert "Database connection lost" in (res.detail or "")


def test_configurable_defaults():
    mock_provider = MagicMock()
    mock_factory = MagicMock()

    service = VectorRetrievalService(
        session_factory=mock_factory,
        embedding_provider=mock_provider,
        default_top_k=5,
        default_distance_threshold=0.75,
    )

    assert service.default_top_k == 5
    assert service.default_distance_threshold == 0.75
