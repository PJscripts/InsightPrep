"""End-to-end ingestion pipeline orchestrating loading, chunking, and embedding."""

import logging
from pathlib import Path

from app.services.rag.chunker import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DocumentChunker,
)
from app.services.rag.document_loader import MarkdownDocumentLoader
from app.services.rag.embeddings import LocalSentenceTransformerEmbeddingProvider
from app.services.rag.ingestion_types import (
    IngestedChunk,
    IngestedDocument,
    IngestionBatchResult,
    ParsedDocument,
)
from app.services.rag.repository_interface import KnowledgePersistenceRepository

logger = logging.getLogger(__name__)


class KnowledgeIngestionService:
    """Orchestrates loading, chunking, embedding, and idempotency for RAG."""

    def __init__(
        self,
        *,
        loader: MarkdownDocumentLoader | None = None,
        chunker: DocumentChunker | None = None,
        embedding_provider: LocalSentenceTransformerEmbeddingProvider | None = None,
        repository: KnowledgePersistenceRepository | None = None,
    ) -> None:
        self.loader = loader or MarkdownDocumentLoader()
        self.chunker = chunker or DocumentChunker(
            chunk_size=DEFAULT_CHUNK_SIZE,
            chunk_overlap=DEFAULT_CHUNK_OVERLAP,
        )
        self.embedding_provider = embedding_provider
        self.repository = repository

    def ingest_document(self, parsed_doc: ParsedDocument) -> IngestedDocument:
        """Process a parsed document into chunks with embeddings if provider given."""
        raw_chunks = self.chunker.chunk_document(parsed_doc)
        processed_chunks: list[IngestedChunk] = []

        for chunk in raw_chunks:
            embedding_vec: tuple[float, ...] | None = None
            embedding_res = None

            if self.embedding_provider is not None:
                embedding_res = self.embedding_provider.embed(chunk.chunk_text)
                if embedding_res.is_available and embedding_res.vector is not None:
                    embedding_vec = embedding_res.vector
                else:
                    logger.warning(
                        "Embedding unavailable for %s chunk %d: %s (%s)",
                        parsed_doc.source_key,
                        chunk.chunk_index,
                        embedding_res.failure_code,
                        embedding_res.detail,
                    )

            processed_chunks.append(
                IngestedChunk(
                    chunk_index=chunk.chunk_index,
                    chunk_text=chunk.chunk_text,
                    content_hash=chunk.content_hash,
                    embedding=embedding_vec,
                    embedding_result=embedding_res,
                )
            )

        return IngestedDocument(
            document=parsed_doc,
            chunks=processed_chunks,
        )

    def ingest_path(self, file_path: Path) -> IngestedDocument:
        """Load and ingest a single markdown file."""
        parsed_doc = self.loader.load_document(file_path)
        return self.ingest_document(parsed_doc)

    def ingest_corpus(self, corpus_dir: Path) -> IngestionBatchResult:
        """Discover and ingest all markdown files in a corpus directory."""
        parsed_documents = self.loader.discover_documents(corpus_dir)
        ingested_documents: list[IngestedDocument] = []
        total_chunks = 0
        failures: list[dict] = []

        for doc in parsed_documents:
            try:
                ingested = self.ingest_document(doc)
                ingested_documents.append(ingested)
                total_chunks += ingested.chunk_count

                # If a repository boundary is supplied, persist or update
                if self.repository is not None:
                    existing_hash = self.repository.get_document_hash(doc.source_key)
                    if existing_hash != doc.content_hash:
                        self.repository.persist_document(ingested)
            except Exception as exc:
                logger.error("Failed to ingest document %s: %s", doc.source_key, exc)
                failures.append({"source_key": doc.source_key, "error": str(exc)})

        return IngestionBatchResult(
            documents=ingested_documents,
            total_chunks=total_chunks,
            failures=failures,
        )
