"""Unit tests for RAG technical answer evaluation integration."""

from unittest.mock import MagicMock

from app.services.mock_answer_evaluator import MockAnswerEvaluator
from app.services.rag.answer_context import AnswerRAGContext
from app.services.rag.answer_context_builder import (
    AnswerRAGContextBuilder,
    construct_evaluation_retrieval_query,
)
from app.services.rag.retrieval_types import (
    RetrievalFailureCode,
    RetrievalResult,
    RetrievedChunk,
)


def _make_dummy_chunk(
    chunk_id: int, topic: str = "dbms", title: str = "ACID Properties"
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id=1,
        chunk_index=0,
        chunk_text=f"Technical reference benchmark for {title}.",
        cosine_distance=0.22,
        similarity_score=0.78,
        source_key="dummy_key",
        title=title,
        topic=topic,
        source_path="dummy.md",
    )


def test_construct_evaluation_retrieval_query():
    query = construct_evaluation_retrieval_query(
        question="Explain ACID properties in database transactions.",
        topic="dbms",
        answer="Atomicity, Consistency, Isolation, Durability.",
    )
    assert "ACID properties" in query
    assert "topic: dbms" in query


def test_answer_rag_context_prompt_formatting():
    chunk = _make_dummy_chunk(1, topic="dbms", title="DBMS Transactions")
    ctx = AnswerRAGContext(query="ACID", topic="dbms", chunks=[chunk])
    assert ctx.has_context
    formatted = ctx.format_for_prompt()
    assert "Reference Technical Material" in formatted
    assert "DBMS Transactions" in formatted
    assert "Reward statements demonstrating understanding" in formatted
    assert "Do NOT mention reference material, retrieval, or RAG" in formatted


def test_hr_interview_bypasses_evaluation_rag():
    mock_retriever = MagicMock()
    builder = AnswerRAGContextBuilder(retrieval_service=mock_retriever)

    res = builder.build_context(
        interview_type="hr",
        question="Tell me about a time you resolved a conflict.",
        answer="I spoke with the team member directly.",
        current_topic="conflict resolution",
    )
    assert res is None
    assert not mock_retriever.retrieve.called


def test_technical_interview_invokes_evaluation_retrieval():
    mock_retriever = MagicMock()
    chunk = _make_dummy_chunk(1, topic="operating_systems", title="Virtual Memory")
    mock_retriever.retrieve.return_value = RetrievalResult.success(
        query="page fault",
        chunks=[chunk],
    )
    builder = AnswerRAGContextBuilder(retrieval_service=mock_retriever)

    res = builder.build_context(
        interview_type="technical",
        question="What happens during a page fault?",
        answer="The OS loads the page from secondary storage.",
        current_topic="virtual memory",
    )
    assert res is not None
    assert res.has_context
    assert len(res.chunks) == 1
    assert res.chunks[0].title == "Virtual Memory"
    assert mock_retriever.retrieve.called


def test_evaluation_retrieval_returns_no_results_fails_open():
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = RetrievalResult.success(
        query="unmatched question",
        chunks=[],
    )
    builder = AnswerRAGContextBuilder(retrieval_service=mock_retriever)

    res = builder.build_context(
        interview_type="technical",
        question="Explain a totally obscure unknown protocol.",
        answer="I don't know.",
    )
    assert res is None


def test_evaluation_retrieval_failure_fails_open():
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = RetrievalResult.unavailable(
        query="failing query",
        failure_code=RetrievalFailureCode.DATABASE_ERROR,
        detail="Database timeout",
    )
    builder = AnswerRAGContextBuilder(retrieval_service=mock_retriever)

    res = builder.build_context(
        interview_type="technical",
        question="Explain B-Trees.",
        answer="A balanced search tree.",
        current_topic="dbms",
    )
    assert res is None


def test_mock_evaluator_compatibility_with_rag_context():
    evaluator = MockAnswerEvaluator()
    chunk = _make_dummy_chunk(1, topic="dbms", title="Indexing")
    rag_ctx = AnswerRAGContext(query="indexing", topic="dbms", chunks=[chunk])

    answer = (
        "A B-tree is a self-balancing tree data structure that maintains "
        "sorted data and allows searches in logarithmic time."
    )
    res = evaluator.evaluate(
        question="How does a B-Tree work?",
        answer=answer,
        resume_analysis={"skills": ["Databases"]},
        rag_context=rag_ctx,
    )
    assert "score" in res
    assert "feedback" in res
    assert "dimensions" in res
    assert res["dimensions"]["technical_knowledge"] > 0.0


def test_evaluate_answer_with_fallback_preserves_routing(monkeypatch):
    """Test RAG context building and evaluator fallback (Groq -> Gemini -> Mock)."""
    from app.api.interviews import evaluate_answer_with_fallback

    session = MagicMock()
    session.id = 456
    session.interview_type = "technical"
    session.current_question = 2
    session.current_topic = "tcp"
    session.evaluation_provider = "groq"

    chunk = _make_dummy_chunk(1, topic="computer_networks", title="TCP Protocols")
    rag_builder = MagicMock()
    rag_builder.build_context.return_value = AnswerRAGContext(
        query="TCP",
        topic="computer_networks",
        chunks=[chunk],
    )

    groq_eval = MagicMock()
    groq_eval.evaluate.side_effect = RuntimeError("Groq down")

    gemini_eval = MagicMock()
    gemini_eval.evaluate.side_effect = RuntimeError("Gemini down")

    mock_eval = MagicMock()
    mock_eval.evaluate.return_value = {
        "score": 8.5,
        "feedback": "Great explanation.",
        "dimensions": {
            "technical_knowledge": 8.5,
            "problem_solving": 8.5,
            "communication": 8.5,
            "clarity": 8.5,
        },
    }

    def fake_get_evaluator(provider):
        if provider == "groq":
            return groq_eval
        if provider == "gemini":
            return gemini_eval
        return mock_eval

    monkeypatch.setattr(
        "app.api.interviews.get_answer_evaluator_for_provider", fake_get_evaluator
    )

    evaluation = evaluate_answer_with_fallback(
        session=session,
        question_text="Explain TCP handshake",
        answer_text="SYN, SYN-ACK, ACK.",
        resume_analysis={"skills": ["Networking"]},
        rag_builder=rag_builder,
    )

    assert evaluation["score"] == 8.5
    assert session.evaluation_provider == "mock"
    # Both groq and gemini should receive the rag_context before failing
    assert groq_eval.evaluate.call_args[1]["rag_context"].has_context
    assert gemini_eval.evaluate.call_args[1]["rag_context"].has_context


def test_groq_evaluator_prompt_incorporates_rag_reference():
    """Verify evaluator injects reference technical material into prompt."""
    from app.services.groq_answer_evaluator import GroqAnswerEvaluator

    chunk = _make_dummy_chunk(1, topic="dbms", title="ACID Properties")
    rag_ctx = AnswerRAGContext(query="ACID", topic="dbms", chunks=[chunk])

    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = (
        '{"score": 9.0, "feedback": "Accurate.", "dimensions": '
        '{"technical_knowledge": 9.0, "problem_solving": 9.0, '
        '"communication": 9.0, "clarity": 9.0}}'
    )
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    evaluator = GroqAnswerEvaluator.__new__(GroqAnswerEvaluator)
    evaluator.client = mock_client

    res = evaluator.evaluate(
        question="What is Atomicity?",
        answer="All or nothing.",
        resume_analysis={"skills": ["SQL"]},
        rag_context=rag_ctx,
    )

    assert res["score"] == 9.0
    prompt_sent = mock_client.chat.completions.create.call_args[1]["messages"][1][
        "content"
    ]
    assert "Reference Technical Material" in prompt_sent
    assert "ACID Properties" in prompt_sent
