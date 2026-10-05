"""Typed contracts for optional RAG dependencies."""

from dataclasses import dataclass
from enum import StrEnum


class EmbeddingStatus(StrEnum):
    """Availability state returned by an embedding provider."""

    AVAILABLE = "available"
    DISABLED = "disabled"
    UNAVAILABLE = "unavailable"


class EmbeddingFailureCode(StrEnum):
    """Machine-readable reason for a non-available embedding result."""

    DISABLED = "disabled"
    MODEL_LOAD_FAILED = "model_load_failed"
    EMBEDDING_FAILED = "embedding_failed"
    INVALID_VECTOR = "invalid_vector"
    INVALID_INPUT = "invalid_input"
    EMPTY_INPUT = "empty_input"


@dataclass(frozen=True, slots=True)
class EmbeddingResult:
    """Result of one embedding attempt without raising into interview flows."""

    status: EmbeddingStatus
    vector: tuple[float, ...] | None = None
    failure_code: EmbeddingFailureCode | None = None
    detail: str | None = None

    @property
    def is_available(self) -> bool:
        return self.status is EmbeddingStatus.AVAILABLE

    @classmethod
    def available(cls, vector: tuple[float, ...]) -> "EmbeddingResult":
        return cls(status=EmbeddingStatus.AVAILABLE, vector=vector)

    @classmethod
    def disabled(cls) -> "EmbeddingResult":
        return cls(
            status=EmbeddingStatus.DISABLED,
            failure_code=EmbeddingFailureCode.DISABLED,
            detail="RAG embeddings are disabled by configuration.",
        )

    @classmethod
    def unavailable(
        cls,
        failure_code: EmbeddingFailureCode,
        detail: str,
    ) -> "EmbeddingResult":
        return cls(
            status=EmbeddingStatus.UNAVAILABLE,
            failure_code=failure_code,
            detail=detail,
        )
