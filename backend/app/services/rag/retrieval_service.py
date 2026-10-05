"""Vector similarity retrieval service powered by pgvector and SQLAlchemy."""

import logging
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import KnowledgeDocument
from app.services.rag.embeddings import LocalSentenceTransformerEmbeddingProvider
from app.services.rag.retrieval_types import (
    RetrievalFailureCode,
    RetrievalResult,
    RetrievedChunk,
)

logger = logging.getLogger(__name__)

DEFAULT_RETRIEVAL_TOP_K = 3
DEFAULT_DISTANCE_THRESHOLD = 0.85  # cosine distance: 0 = identical, 1 = orthogonal


class VectorRetrievalService:
    """Retrieves relevant knowledge chunks using vector embeddings and pgvector."""

    def __init__(
        self,
        *,
        session_factory: Callable[[], Session],
        embedding_provider: LocalSentenceTransformerEmbeddingProvider,
        default_top_k: int = DEFAULT_RETRIEVAL_TOP_K,
        default_distance_threshold: float = DEFAULT_DISTANCE_THRESHOLD,
    ) -> None:
        self.session_factory = session_factory
        self.embedding_provider = embedding_provider
        self.default_top_k = default_top_k
        self.default_distance_threshold = default_distance_threshold

    def retrieve(
        self,
        query: str,
        *,
        top_k: int | None = None,
        distance_threshold: float | None = None,
        topic: str | None = None,
    ) -> RetrievalResult:
        """Search for top_k most similar chunks matching the query string.

        Fail-open behavior: Returns typed unavailable RetrievalResult on any error
        without raising exceptions into interview flows.
        """
        if not isinstance(query, str) or not query.strip():
            return RetrievalResult.unavailable(
                query=query if isinstance(query, str) else "",
                failure_code=RetrievalFailureCode.INVALID_QUERY,
                detail="Query must be a non-empty string.",
            )

        k = top_k if top_k is not None and top_k > 0 else self.default_top_k
        threshold = (
            distance_threshold
            if distance_threshold is not None
            else self.default_distance_threshold
        )

        # 1. Generate query embedding
        try:
            embedding_res = self.embedding_provider.embed(query)
            if not embedding_res.is_available or embedding_res.vector is None:
                err_detail = (
                    f"Embedding failed: {embedding_res.failure_code} "
                    f"({embedding_res.detail})"
                )
                return RetrievalResult.unavailable(
                    query=query,
                    failure_code=RetrievalFailureCode.EMBEDDING_FAILED,
                    detail=err_detail,
                )
            query_vector = list(embedding_res.vector)
        except Exception as exc:
            logger.exception(
                "Unexpected error during query embedding generation: %s", exc
            )
            return RetrievalResult.unavailable(
                query=query,
                failure_code=RetrievalFailureCode.EMBEDDING_FAILED,
                detail=f"Embedding exception: {exc}",
            )

        # 2. Query database for nearest neighbors
        try:
            with self.session_factory() as session:
                distance_expr = KnowledgeChunk.embedding.cosine_distance(query_vector)

                stmt = (
                    select(
                        KnowledgeChunk.id.label("chunk_id"),
                        KnowledgeChunk.document_id,
                        KnowledgeChunk.chunk_index,
                        KnowledgeChunk.chunk_text,
                        distance_expr.label("distance"),
                        KnowledgeDocument.source_key,
                        KnowledgeDocument.title,
                        KnowledgeDocument.topic,
                        KnowledgeDocument.source_path,
                    )
                    .join(
                        KnowledgeDocument,
                        KnowledgeChunk.document_id == KnowledgeDocument.id,
                    )
                    .where(KnowledgeChunk.embedding.is_not(None))
                )

                if topic:
                    stmt = stmt.where(KnowledgeDocument.topic == topic)

                if threshold is not None:
                    stmt = stmt.where(distance_expr <= threshold)

                stmt = stmt.order_by(distance_expr).limit(k)

                rows = session.execute(stmt).fetchall()

                retrieved_chunks: list[RetrievedChunk] = []
                for row in rows:
                    dist = float(row.distance)
                    # Cosine similarity for normalized vectors: 1 - cosine_distance
                    sim_score = round(max(0.0, 1.0 - dist), 4)

                    retrieved_chunks.append(
                        RetrievedChunk(
                            chunk_id=row.chunk_id,
                            document_id=row.document_id,
                            chunk_index=row.chunk_index,
                            chunk_text=row.chunk_text,
                            cosine_distance=round(dist, 4),
                            similarity_score=sim_score,
                            source_key=row.source_key,
                            title=row.title,
                            topic=row.topic,
                            source_path=row.source_path or "",
                        )
                    )

                return RetrievalResult.success(query=query, chunks=retrieved_chunks)

        except Exception as exc:
            logger.exception("Database error during vector retrieval: %s", exc)
            return RetrievalResult.unavailable(
                query=query,
                failure_code=RetrievalFailureCode.DATABASE_ERROR,
                detail=f"Database retrieval error: {exc}",
            )
