"""Optional retrieval-augmented generation support services."""

from app.services.rag.answer_context import AnswerRAGContext
from app.services.rag.answer_context_builder import (
    AnswerRAGContextBuilder,
    construct_evaluation_retrieval_query,
)
from app.services.rag.chunker import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DocumentChunker,
)
from app.services.rag.document_loader import (
    DocumentParsingError,
    MarkdownDocumentLoader,
    compute_content_hash,
)
from app.services.rag.embeddings import LocalSentenceTransformerEmbeddingProvider
from app.services.rag.ingestion_service import KnowledgeIngestionService
from app.services.rag.ingestion_types import (
    IngestedChunk,
    IngestedDocument,
    IngestionBatchResult,
    ParsedDocument,
)
from app.services.rag.question_context import QuestionRAGContext
from app.services.rag.question_context_builder import (
    CORPUS_TOPIC_MAP,
    QuestionRAGContextBuilder,
    construct_retrieval_query,
    map_topic_to_corpus,
)
from app.services.rag.repository_interface import KnowledgePersistenceRepository
from app.services.rag.retrieval_service import (
    DEFAULT_DISTANCE_THRESHOLD,
    DEFAULT_RETRIEVAL_TOP_K,
    VectorRetrievalService,
)
from app.services.rag.retrieval_types import (
    RetrievalFailureCode,
    RetrievalResult,
    RetrievalStatus,
    RetrievedChunk,
)
from app.services.rag.sqlalchemy_repository import SqlAlchemyKnowledgeRepository
from app.services.rag.types import (
    EmbeddingFailureCode,
    EmbeddingResult,
    EmbeddingStatus,
)

__all__ = [
    "AnswerRAGContext",
    "AnswerRAGContextBuilder",
    "CORPUS_TOPIC_MAP",
    "DEFAULT_CHUNK_OVERLAP",
    "DEFAULT_CHUNK_SIZE",
    "DEFAULT_DISTANCE_THRESHOLD",
    "DEFAULT_RETRIEVAL_TOP_K",
    "DocumentChunker",
    "DocumentParsingError",
    "EmbeddingFailureCode",
    "EmbeddingResult",
    "EmbeddingStatus",
    "IngestedChunk",
    "IngestedDocument",
    "IngestionBatchResult",
    "KnowledgeIngestionService",
    "KnowledgePersistenceRepository",
    "LocalSentenceTransformerEmbeddingProvider",
    "MarkdownDocumentLoader",
    "ParsedDocument",
    "QuestionRAGContext",
    "QuestionRAGContextBuilder",
    "RetrievalFailureCode",
    "RetrievalResult",
    "RetrievalStatus",
    "RetrievedChunk",
    "SqlAlchemyKnowledgeRepository",
    "VectorRetrievalService",
    "compute_content_hash",
    "construct_evaluation_retrieval_query",
    "construct_retrieval_query",
    "map_topic_to_corpus",
]
