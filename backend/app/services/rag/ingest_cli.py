"""CLI command / script to execute knowledge corpus ingestion against a database."""

import argparse
import logging
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.services.rag.chunker import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DocumentChunker,
)
from app.services.rag.document_loader import MarkdownDocumentLoader
from app.services.rag.embeddings import LocalSentenceTransformerEmbeddingProvider
from app.services.rag.ingestion_service import KnowledgeIngestionService
from app.services.rag.sqlalchemy_repository import SqlAlchemyKnowledgeRepository

logger = logging.getLogger(__name__)


def ingest_corpus(
    db_url: str,
    corpus_dir: Path | None = None,
    repo_root: Path | None = None,
    embedding_enabled: bool = True,
) -> int:
    """Ingest markdown corpus into the specified database."""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[4]
    if corpus_dir is None:
        corpus_dir = repo_root / "docs" / "knowledge"

    print(f"Connecting to database: {db_url}")
    print(f"Ingesting corpus from: {corpus_dir}")

    engine = create_engine(db_url, pool_pre_ping=True)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    repository = SqlAlchemyKnowledgeRepository(session_factory=session_factory)
    embedding_provider = LocalSentenceTransformerEmbeddingProvider(
        enabled=embedding_enabled,
        dimensions=384,
    )
    loader = MarkdownDocumentLoader(repo_root=repo_root)
    chunker = DocumentChunker(
        chunk_size=DEFAULT_CHUNK_SIZE,
        chunk_overlap=DEFAULT_CHUNK_OVERLAP,
    )

    service = KnowledgeIngestionService(
        loader=loader,
        chunker=chunker,
        embedding_provider=embedding_provider,
        repository=repository,
    )

    batch_result = service.ingest_corpus(corpus_dir)
    print("Ingestion finished.")
    print(f"  Documents processed: {len(batch_result.documents)}")
    print(f"  Total chunks: {batch_result.total_chunks}")
    print(f"  Failures: {len(batch_result.failures)}")

    if batch_result.failures:
        for f in batch_result.failures:
            print(f"    ERROR [{f.get('source_key')}]: {f.get('error')}")
        return 1

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest RAG knowledge corpus into database."
    )
    parser.add_argument(
        "--db-url",
        type=str,
        required=True,
        help="Database URL to ingest corpus into.",
    )
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        default=None,
        help="Path to knowledge directory.",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    code = ingest_corpus(db_url=args.db_url, corpus_dir=args.corpus_dir)
    sys.exit(code)


if __name__ == "__main__":
    main()
