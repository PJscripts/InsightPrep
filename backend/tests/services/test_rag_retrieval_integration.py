"""Integration tests for VectorRetrievalService against isolated pgvector database.

Explicitly targets localhost:5434 (rag_test_db).
Skipped automatically if the isolated container is unavailable.
Never connects to localhost:5433 or the production database.
"""

import os
from collections.abc import Callable

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.services.rag.embeddings import LocalSentenceTransformerEmbeddingProvider
from app.services.rag.retrieval_service import VectorRetrievalService

ISOLATED_DB_URL = os.getenv(
    "ISOLATED_RAG_DATABASE_URL",
    "postgresql+psycopg://rag_user:rag_password@localhost:5434/rag_test_db",
)


@pytest.fixture(scope="module")
def isolated_session_factory() -> Callable[[], Session]:
    """Provide sessionmaker connected to isolated database on port 5434."""
    try:
        engine = create_engine(ISOLATED_DB_URL, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
    except Exception as exc:
        pytest.skip(
            f"Isolated pgvector database not reachable at {ISOLATED_DB_URL}: {exc}"
        )

    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="module")
def real_retriever(isolated_session_factory) -> VectorRetrievalService:
    provider = LocalSentenceTransformerEmbeddingProvider(
        enabled=True,
        dimensions=384,
    )
    return VectorRetrievalService(
        session_factory=isolated_session_factory,
        embedding_provider=provider,
        default_top_k=2,
    )


@pytest.mark.parametrize(
    ("query", "expected_topic", "expected_key"),
    [
        (
            "What are the ACID properties of a database transaction?",
            "dbms",
            "dbms_acid_transactions",
        ),
        (
            "How does the TCP three-way handshake work?",
            "computer_networks",
            "cn_tcp_udp_reliable_transport",
        ),
        (
            "What is a TLB in virtual memory?",
            "operating_systems",
            "os_virtual_memory_paging",
        ),
        (
            "How does a hash table handle collisions?",
            "dsa",
            "dsa_arrays_hashing",
        ),
        (
            "What is the difference between BFS and DFS?",
            "dsa",
            "dsa_trees_graphs",
        ),
    ],
)
def test_evaluation_queries_retrieve_relevant_chunks(
    real_retriever: VectorRetrievalService,
    query: str,
    expected_topic: str,
    expected_key: str,
):
    """Verify each evaluation query returns relevant top results with provenance."""
    result = real_retriever.retrieve(query, top_k=2)

    assert result.is_success, f"Retrieval failed for query: {query}"
    assert len(result.chunks) >= 1

    top_chunk = result.chunks[0]
    assert top_chunk.source_key == expected_key
    assert top_chunk.topic == expected_topic
    assert top_chunk.title != ""
    assert top_chunk.source_path.startswith("docs/knowledge/")
    assert 0.0 <= top_chunk.cosine_distance <= 1.0
    assert 0.0 <= top_chunk.similarity_score <= 1.0


def test_topic_filtering(real_retriever: VectorRetrievalService):
    """Verify topic filtering strictly restricts results to specified topic."""
    query = "What is a tree traversal?"
    res_dsa = real_retriever.retrieve(query, topic="dsa", top_k=3)
    assert res_dsa.is_success
    assert len(res_dsa.chunks) > 0
    for chunk in res_dsa.chunks:
        assert chunk.topic == "dsa"

    res_dbms = real_retriever.retrieve(query, topic="dbms", top_k=3)
    assert res_dbms.is_success
    for chunk in res_dbms.chunks:
        assert chunk.topic == "dbms"
