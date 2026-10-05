"""Integration tests for RAG answer evaluation against isolated pgvector database.

Explicitly targets localhost:5434 (rag_test_db).
Skipped automatically if the isolated container is unavailable.
Never connects to localhost:5433 or the production database.
"""

import os
from collections.abc import Callable

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.services.mock_answer_evaluator import MockAnswerEvaluator
from app.services.rag.answer_context_builder import AnswerRAGContextBuilder
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
def real_answer_builder(isolated_session_factory) -> AnswerRAGContextBuilder:
    provider = LocalSentenceTransformerEmbeddingProvider(
        enabled=True,
        dimensions=384,
    )
    retriever = VectorRetrievalService(
        session_factory=isolated_session_factory,
        embedding_provider=provider,
        default_top_k=2,
    )
    return AnswerRAGContextBuilder(retrieval_service=retriever)


def test_integration_eval_dbms_acid(real_answer_builder: AnswerRAGContextBuilder):
    """Test A: DBMS / ACID Question and Answer retrieval."""
    question = "Explain the ACID properties of a database transaction."
    answer = (
        "Atomicity means a transaction is all-or-nothing, consistency preserves "
        "valid database states, isolation controls how concurrent transactions "
        "interact, and durability means committed changes survive failures."
    )
    ctx = real_answer_builder.build_context(
        interview_type="technical",
        question=question,
        answer=answer,
        current_topic="ACID Properties",
    )
    assert ctx is not None
    assert ctx.has_context
    assert any(
        "acid" in c.source_key.lower() or "transaction" in c.source_key.lower()
        for c in ctx.chunks
    )

    # Verify evaluator evaluates successfully with context
    evaluator = MockAnswerEvaluator()
    res = evaluator.evaluate(
        question=question,
        answer=answer,
        resume_analysis={"skills": ["PostgreSQL"]},
        rag_context=ctx,
    )
    assert res["score"] >= 7.0
    assert "technical_knowledge" in res["dimensions"]


def test_integration_eval_cn_tcp(real_answer_builder: AnswerRAGContextBuilder):
    """Test B: Computer Networks / TCP handshake retrieval."""
    question = "Explain the TCP three-way handshake."
    answer = (
        "TCP establishes a connection using SYN, SYN-ACK, and ACK, allowing both "
        "sides to synchronize sequence numbers."
    )
    ctx = real_answer_builder.build_context(
        interview_type="technical",
        question=question,
        answer=answer,
        current_topic="TCP",
    )
    assert ctx is not None
    assert ctx.has_context
    assert any("tcp" in c.source_key.lower() for c in ctx.chunks)


def test_integration_eval_os_virtual_memory(
    real_answer_builder: AnswerRAGContextBuilder,
):
    """Test C: Operating Systems / Virtual Memory page fault retrieval."""
    question = "What happens during a page fault?"
    answer = (
        "The OS detects the missing page, loads it from secondary storage into a "
        "physical frame, updates the page table, and resumes execution."
    )
    ctx = real_answer_builder.build_context(
        interview_type="technical",
        question=question,
        answer=answer,
        current_topic="Virtual Memory",
    )
    assert ctx is not None
    assert ctx.has_context
    assert any("virtual_memory" in c.source_key.lower() for c in ctx.chunks)


def test_integration_eval_hr_bypasses(
    real_answer_builder: AnswerRAGContextBuilder,
):
    """Test D: HR Question bypasses technical retrieval."""
    question = "Tell me about a time you resolved a conflict in a team."
    answer = "I actively listened to both parties and found common ground."
    ctx = real_answer_builder.build_context(
        interview_type="hr",
        question=question,
        answer=answer,
        current_topic="conflict resolution",
    )
    assert ctx is None


def test_integration_eval_rag_unavailable_fail_open():
    """Verify evaluation succeeds even when RAG retrieval service is unavailable."""
    failing_builder = AnswerRAGContextBuilder(retrieval_service=None)
    question = "Explain the ACID properties of a database transaction."
    answer = "Atomicity, Consistency, Isolation, Durability."

    ctx = failing_builder.build_context(
        interview_type="technical",
        question=question,
        answer=answer,
        current_topic="ACID",
    )
    assert ctx is None

    # Evaluator still evaluates cleanly with rag_context=None
    evaluator = MockAnswerEvaluator()
    res = evaluator.evaluate(
        question=question,
        answer=answer,
        resume_analysis={"skills": ["SQL"]},
        rag_context=ctx,
    )
    assert res["score"] > 0
    assert "dimensions" in res
