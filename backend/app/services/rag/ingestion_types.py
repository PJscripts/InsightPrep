"""Data transfer objects and results for knowledge ingestion."""

from dataclasses import dataclass
from typing import Any

from app.services.rag.types import EmbeddingResult


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    """A markdown document successfully discovered and parsed from disk."""

    source_key: str
    title: str
    topic: str
    source_origin: str
    source_license: str
    source_path: str
    content_hash: str
    body: str


@dataclass(frozen=True, slots=True)
class IngestedChunk:
    """A discrete knowledge chunk with deterministic content and optional embedding."""

    chunk_index: int
    chunk_text: str
    content_hash: str
    embedding: tuple[float, ...] | None = None
    embedding_result: EmbeddingResult | None = None


@dataclass(frozen=True, slots=True)
class IngestedDocument:
    """An ingested knowledge document containing parsed metadata and discrete chunks."""

    document: ParsedDocument
    chunks: list[IngestedChunk]

    @property
    def source_key(self) -> str:
        return self.document.source_key

    @property
    def content_hash(self) -> str:
        return self.document.content_hash

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)


@dataclass(frozen=True, slots=True)
class IngestionBatchResult:
    """Aggregated result of an ingestion run across multiple documents."""

    documents: list[IngestedDocument]
    total_chunks: int
    failures: list[dict[str, Any]]
