"""Typed contracts for vector similarity retrieval."""

from dataclasses import dataclass
from enum import StrEnum


class RetrievalStatus(StrEnum):
    """Availability state of a retrieval query."""

    SUCCESS = "success"
    DISABLED = "disabled"
    UNAVAILABLE = "unavailable"


class RetrievalFailureCode(StrEnum):
    """Reason for a non-success retrieval response."""

    DISABLED = "disabled"
    INVALID_QUERY = "invalid_query"
    EMBEDDING_FAILED = "embedding_failed"
    DATABASE_ERROR = "database_error"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    """A single retrieved knowledge chunk with distance, similarity, and provenance."""

    chunk_id: int
    document_id: int
    chunk_index: int
    chunk_text: str
    cosine_distance: float
    similarity_score: float
    source_key: str
    title: str
    topic: str
    source_path: str


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    """Result of a retrieval search attempt with fail-open status."""

    status: RetrievalStatus
    query: str
    chunks: list[RetrievedChunk]
    failure_code: RetrievalFailureCode | None = None
    detail: str | None = None

    @property
    def is_success(self) -> bool:
        return self.status is RetrievalStatus.SUCCESS

    @classmethod
    def success(cls, query: str, chunks: list[RetrievedChunk]) -> "RetrievalResult":
        return cls(status=RetrievalStatus.SUCCESS, query=query, chunks=chunks)

    @classmethod
    def disabled(cls, query: str) -> "RetrievalResult":
        return cls(
            status=RetrievalStatus.DISABLED,
            query=query,
            chunks=[],
            failure_code=RetrievalFailureCode.DISABLED,
            detail="Retrieval is disabled.",
        )

    @classmethod
    def unavailable(
        cls,
        query: str,
        failure_code: RetrievalFailureCode,
        detail: str,
    ) -> "RetrievalResult":
        return cls(
            status=RetrievalStatus.UNAVAILABLE,
            query=query,
            chunks=[],
            failure_code=failure_code,
            detail=detail,
        )
