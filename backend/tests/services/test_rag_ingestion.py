"""Comprehensive tests for RAG knowledge ingestion and chunking pipeline."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

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
from app.services.rag.types import EmbeddingFailureCode

REPO_ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE_DIR = REPO_ROOT / "docs" / "knowledge"


@pytest.fixture
def temp_doc(tmp_path: Path):
    """Factory fixture for creating temporary markdown documents."""

    def _create(
        filename: str = "doc.md",
        source_key: str = "test_key",
        title: str = "Test Title",
        topic: str = "dsa",
        source_origin: str = "InsightPrep",
        source_license: str = "project-authored",
        body: str = "# Section 1\n\nContent paragraph.",
    ) -> Path:
        file_path = tmp_path / filename
        content = (
            f"---\n"
            f"source_key: {source_key}\n"
            f"title: {title}\n"
            f"topic: {topic}\n"
            f"source_origin: {source_origin}\n"
            f"source_license: {source_license}\n"
            f"---\n\n"
            f"{body}"
        )
        file_path.write_text(content, encoding="utf-8")
        return file_path

    return _create


# ===========================================================================
# 1. Document Loading and Frontmatter Parsing Tests
# ===========================================================================


def test_valid_frontmatter_parsing(temp_doc):
    loader = MarkdownDocumentLoader(repo_root=REPO_ROOT)
    doc_path = temp_doc(
        filename="arrays.md",
        source_key="dsa_arrays",
        title="Arrays in DSA",
        topic="dsa",
        source_origin="InsightPrep Unit Test",
        source_license="project-authored",
        body="# Heading\n\nBody content goes here.",
    )

    parsed = loader.load_document(doc_path)
    assert parsed.source_key == "dsa_arrays"
    assert parsed.title == "Arrays in DSA"
    assert parsed.topic == "dsa"
    assert parsed.source_origin == "InsightPrep Unit Test"
    assert parsed.source_license == "project-authored"
    assert parsed.body == "# Heading\n\nBody content goes here."
    assert len(parsed.content_hash) == 64


def test_missing_required_metadata(tmp_path):
    loader = MarkdownDocumentLoader(repo_root=REPO_ROOT)
    bad_doc = tmp_path / "bad.md"
    bad_doc.write_text(
        "---\ntitle: Missing Key\ntopic: dsa\n---\n\nSome body text",
        encoding="utf-8",
    )

    with pytest.raises(
        DocumentParsingError, match="Missing or empty required metadata field"
    ):
        loader.load_document(bad_doc)


def test_malformed_frontmatter(tmp_path):
    loader = MarkdownDocumentLoader(repo_root=REPO_ROOT)
    bad_doc = tmp_path / "malformed.md"
    bad_doc.write_text(
        "---\nkey: : broken yaml\n---\n\nBody",
        encoding="utf-8",
    )

    with pytest.raises(DocumentParsingError, match="Malformed YAML frontmatter"):
        loader.load_document(bad_doc)


def test_missing_frontmatter_delimiters(tmp_path):
    loader = MarkdownDocumentLoader(repo_root=REPO_ROOT)
    doc = tmp_path / "no_frontmatter.md"
    doc.write_text("# Just Markdown\n\nNo frontmatter here.", encoding="utf-8")

    with pytest.raises(DocumentParsingError, match="missing valid YAML frontmatter"):
        loader.load_document(doc)


def test_empty_document_handling(tmp_path):
    loader = MarkdownDocumentLoader(repo_root=REPO_ROOT)
    empty_doc = tmp_path / "empty.md"
    empty_doc.write_text("", encoding="utf-8")

    with pytest.raises(DocumentParsingError, match="Document is empty"):
        loader.load_document(empty_doc)


def test_empty_body_after_frontmatter(tmp_path):
    loader = MarkdownDocumentLoader(repo_root=REPO_ROOT)
    doc = tmp_path / "empty_body.md"
    doc.write_text(
        "---\n"
        "source_key: test\n"
        "title: T\n"
        "topic: dsa\n"
        "source_origin: O\n"
        "source_license: L\n"
        "---\n\n   \n",
        encoding="utf-8",
    )

    with pytest.raises(
        DocumentParsingError, match="Document body is empty after frontmatter"
    ):
        loader.load_document(doc)


def test_source_path_derivation(temp_doc):
    loader = MarkdownDocumentLoader(repo_root=REPO_ROOT)
    doc_path = temp_doc(filename="sample.md")
    parsed = loader.load_document(doc_path)
    assert parsed.source_path is not None
    assert isinstance(parsed.source_path, str)


def test_deterministic_sha256_hashing():
    text1 = "This is a body of technical documentation."
    text2 = "This is a body of technical documentation.\r\n"
    text3 = "  This is a body of technical documentation.  \n"

    h1 = compute_content_hash(text1)
    h2 = compute_content_hash(text2)
    h3 = compute_content_hash(text3)

    assert h1 == h2 == h3
    assert len(h1) == 64
    assert h1 != compute_content_hash("Different documentation.")


# ===========================================================================
# 2. Chunking Tests
# ===========================================================================


def test_deterministic_chunking(temp_doc):
    loader = MarkdownDocumentLoader(repo_root=REPO_ROOT)
    chunker = DocumentChunker(chunk_size=120, chunk_overlap=20)

    long_body = (
        "# Topic 1\n\n"
        "Paragraph one explaining concepts with length to test splitting.\n\n"
        "## Subtopic A\n\n"
        "Second paragraph covering details on algorithms and system invariants.\n\n"
        "## Subtopic B\n\n"
        "Third paragraph explaining practical engineering trade-offs."
    )
    doc = loader.load_document(temp_doc(body=long_body))

    chunks_first_run = chunker.chunk_document(doc)
    chunks_second_run = chunker.chunk_document(doc)

    assert len(chunks_first_run) > 1
    assert len(chunks_first_run) == len(chunks_second_run)
    for c1, c2 in zip(chunks_first_run, chunks_second_run, strict=True):
        assert c1.chunk_index == c2.chunk_index
        assert c1.chunk_text == c2.chunk_text
        assert c1.content_hash == c2.content_hash


def test_chunk_ordering_and_no_empty_chunks(temp_doc):
    loader = MarkdownDocumentLoader(repo_root=REPO_ROOT)
    chunker = DocumentChunker(chunk_size=90, chunk_overlap=15)

    body = (
        "# Heading 1\n\n"
        "Content paragraph A with some words.\n\n"
        "# Heading 2\n\n"
        "Content paragraph B with different information.\n\n"
        "# Heading 3\n\n"
        "Content paragraph C with concluding remarks."
    )
    doc = loader.load_document(temp_doc(body=body))
    chunks = chunker.chunk_document(doc)

    assert len(chunks) >= 2
    for idx, chunk in enumerate(chunks):
        assert chunk.chunk_index == idx
        assert len(chunk.chunk_text.strip()) > 0
        assert len(chunk.content_hash) == 64


def test_overlap_behavior():
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=30)
    text = (
        "# Section 1\n\n"
        "Alpha beta gamma delta epsilon zeta eta theta iota kappa.\n\n"
        "# Section 2\n\n"
        "Lambda mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega."
    )
    chunks = chunker.split_text(text)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 150  # respects budget within reasonable atomic unit bounds


def test_invalid_chunker_params():
    with pytest.raises(ValueError, match="chunk_size must be a positive integer"):
        DocumentChunker(chunk_size=0)

    with pytest.raises(ValueError, match="chunk_overlap must be non-negative"):
        DocumentChunker(chunk_size=100, chunk_overlap=-1)

    with pytest.raises(ValueError, match="strictly less than chunk_size"):
        DocumentChunker(chunk_size=100, chunk_overlap=100)


# ===========================================================================
# 3. Ingestion Pipeline & Embedding Tests
# ===========================================================================


def test_embedding_generation_through_existing_provider(temp_doc):
    mock_model = MagicMock()
    mock_model.encode.return_value = [[0.1] * 384]

    provider = LocalSentenceTransformerEmbeddingProvider(
        enabled=True,
        dimensions=384,
        model_loader=lambda _name: mock_model,
    )

    loader = MarkdownDocumentLoader(repo_root=REPO_ROOT)
    service = KnowledgeIngestionService(
        loader=loader,
        chunker=DocumentChunker(chunk_size=500, chunk_overlap=50),
        embedding_provider=provider,
    )

    doc_path = temp_doc(body="# Section\n\nParagraph text for embedding.")
    ingested = service.ingest_path(doc_path)

    assert ingested.chunk_count >= 1
    for chunk in ingested.chunks:
        assert chunk.embedding is not None
        assert len(chunk.embedding) == 384
        assert chunk.embedding_result is not None
        assert chunk.embedding_result.is_available


def test_embedding_failure_handling(temp_doc):
    def failing_loader(_name: str):
        raise RuntimeError("Model download failed")

    provider = LocalSentenceTransformerEmbeddingProvider(
        enabled=True,
        dimensions=384,
        model_loader=failing_loader,
    )

    loader = MarkdownDocumentLoader(repo_root=REPO_ROOT)
    service = KnowledgeIngestionService(
        loader=loader,
        chunker=DocumentChunker(chunk_size=500, chunk_overlap=50),
        embedding_provider=provider,
    )

    doc_path = temp_doc(body="# Section\n\nParagraph text when model fails.")
    ingested = service.ingest_path(doc_path)

    assert ingested.chunk_count >= 1
    for chunk in ingested.chunks:
        assert chunk.embedding is None
        assert chunk.embedding_result is not None
        assert not chunk.embedding_result.is_available
        assert (
            chunk.embedding_result.failure_code
            == EmbeddingFailureCode.MODEL_LOAD_FAILED
        )


def test_ingestion_of_all_current_corpus_documents():
    """Verify discovery, parsing, and chunking on all 8 corpus files."""
    mock_model = MagicMock()
    # Return 384-dim dummy vector for any chunk
    mock_model.encode.side_effect = lambda texts, **_: [[0.05] * 384 for _ in texts]

    provider = LocalSentenceTransformerEmbeddingProvider(
        enabled=True,
        dimensions=384,
        model_loader=lambda _name: mock_model,
    )

    service = KnowledgeIngestionService(
        loader=MarkdownDocumentLoader(repo_root=REPO_ROOT),
        chunker=DocumentChunker(
            chunk_size=DEFAULT_CHUNK_SIZE, chunk_overlap=DEFAULT_CHUNK_OVERLAP
        ),
        embedding_provider=provider,
    )

    result = service.ingest_corpus(KNOWLEDGE_DIR)

    assert len(result.failures) == 0, f"Ingestion failures: {result.failures}"
    assert len(result.documents) == 8, (
        f"Expected 8 documents, got {len(result.documents)}"
    )
    assert result.total_chunks > 0

    topics = {doc.document.topic for doc in result.documents}
    assert topics == {"dsa", "dbms", "operating_systems", "computer_networks"}

    for doc in result.documents:
        assert doc.chunk_count >= 1
        for chunk in doc.chunks:
            assert chunk.embedding is not None
            assert len(chunk.embedding) == 384
            assert len(chunk.content_hash) == 64
            assert chunk.chunk_index >= 0
