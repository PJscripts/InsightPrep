"""Unit tests for RAG technical question generation integration."""

from unittest.mock import MagicMock

from app.services.mock_question_generator import MockQuestionGenerator
from app.services.rag.question_context import QuestionRAGContext
from app.services.rag.question_context_builder import (
    QuestionRAGContextBuilder,
    construct_retrieval_query,
    map_topic_to_corpus,
)
from app.services.rag.retrieval_types import (
    RetrievalFailureCode,
    RetrievalResult,
    RetrievedChunk,
)


def _make_dummy_chunk(
    chunk_id: int, topic: str = "dsa", title: str = "DSA Topic"
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id=1,
        chunk_index=0,
        chunk_text=f"This is technical content for {title}.",
        cosine_distance=0.25,
        similarity_score=0.75,
        source_key="dummy_key",
        title=title,
        topic=topic,
        source_path="dummy.md",
    )


def test_topic_mapping():
    assert map_topic_to_corpus("data structures") == "dsa"
    assert map_topic_to_corpus("b-trees") == "dbms"
    assert map_topic_to_corpus("virtual memory") == "operating_systems"
    assert map_topic_to_corpus("tcp") == "computer_networks"
    assert map_topic_to_corpus("behavioral teamwork") is None
    assert map_topic_to_corpus(None) is None


def test_construct_retrieval_query():
    query = construct_retrieval_query(
        current_topic="B-Trees",
        difficulty="hard",
        question_strategy="fixed_independent",
    )
    assert "B-Trees" in query
    assert "hard" in query


def test_rag_context_prompt_formatting():
    chunk = _make_dummy_chunk(1, topic="dbms", title="ACID Properties")
    ctx = QuestionRAGContext(query="ACID", topic="dbms", chunks=[chunk])
    assert ctx.has_context
    formatted = ctx.format_for_prompt()
    assert "Reference Technical Material" in formatted
    assert "ACID Properties" in formatted
    assert "Do NOT copy the reference material verbatim" in formatted


def test_hr_interview_bypasses_rag():
    mock_retriever = MagicMock()
    builder = QuestionRAGContextBuilder(retrieval_service=mock_retriever)

    # HR interview should immediately return None without calling retriever
    res = builder.build_context(
        interview_type="hr",
        current_topic="teamwork",
        difficulty="medium",
    )
    assert res is None
    assert not mock_retriever.retrieve.called


def test_technical_interview_invokes_retrieval():
    mock_retriever = MagicMock()
    chunk = _make_dummy_chunk(1, topic="dsa", title="Hash Tables")
    mock_retriever.retrieve.return_value = RetrievalResult.success(
        query="hash tables",
        chunks=[chunk],
    )
    builder = QuestionRAGContextBuilder(retrieval_service=mock_retriever)

    res = builder.build_context(
        interview_type="technical",
        current_topic="hash tables",
        difficulty="medium",
    )
    assert res is not None
    assert res.has_context
    assert len(res.chunks) == 1
    assert res.chunks[0].title == "Hash Tables"
    assert mock_retriever.retrieve.called


def test_retrieval_returns_no_results_fails_open():
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = RetrievalResult.success(
        query="obscure topic",
        chunks=[],
    )
    builder = QuestionRAGContextBuilder(retrieval_service=mock_retriever)

    res = builder.build_context(
        interview_type="technical",
        current_topic="obscure topic",
        difficulty="medium",
    )
    assert res is None


def test_retrieval_failure_fails_open():
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = RetrievalResult.unavailable(
        query="failing query",
        failure_code=RetrievalFailureCode.EMBEDDING_FAILED,
        detail="Model failed",
    )
    builder = QuestionRAGContextBuilder(retrieval_service=mock_retriever)

    res = builder.build_context(
        interview_type="technical",
        current_topic="failing query",
        difficulty="hard",
    )
    assert res is None


def test_retrieval_service_none_returns_none():
    builder = QuestionRAGContextBuilder(retrieval_service=None)
    res = builder.build_context(
        interview_type="technical",
        current_topic="indexing",
        difficulty="medium",
    )
    assert res is None


def test_mock_question_generator_with_rag_context():
    generator = MockQuestionGenerator()
    chunk = _make_dummy_chunk(1, topic="dbms", title="Indexing")
    rag_ctx = QuestionRAGContext(query="indexing", topic="dbms", chunks=[chunk])

    question = generator.generate_question(
        resume_analysis={"skills": ["PostgreSQL"]},
        interview_type="technical",
        difficulty="hard",
        question_number=1,
        current_topic="Indexing",
        rag_context=rag_ctx,
    )
    assert "Indexing" in question
    assert isinstance(question, str)


def test_generate_question_with_fallback_preserves_routing(monkeypatch):
    """Test RAG context building and provider fallback (Groq -> Gemini -> Mock)."""
    from unittest.mock import MagicMock

    from app.api.interviews import generate_question_with_fallback

    # Mock session
    session = MagicMock()
    session.id = 123
    session.interview_type = "technical"
    session.difficulty = "medium"
    session.current_question = 1
    session.current_topic = "B-Trees"
    session.covered_topics = []
    session.question_provider = "groq"

    # Mock DB
    db = MagicMock()

    # Mock RAG builder
    chunk = _make_dummy_chunk(1, topic="dbms", title="Indexing and B-Trees")
    rag_builder = MagicMock()
    rag_builder.build_context.return_value = QuestionRAGContext(
        query="B-Trees",
        topic="dbms",
        chunks=[chunk],
    )

    # Groq fails, Gemini fails, Mock succeeds
    groq_gen = MagicMock()
    groq_gen.generate_question.side_effect = RuntimeError("Groq rate limited")

    gemini_gen = MagicMock()
    gemini_gen.generate_question.side_effect = RuntimeError("Gemini quota exceeded")

    mock_gen = MagicMock()
    mock_gen.generate_question.return_value = "What is your experience with B-Trees?"

    def fake_get_generator(provider):
        if provider == "groq":
            return groq_gen
        if provider == "gemini":
            return gemini_gen
        return mock_gen

    monkeypatch.setattr(
        "app.api.interviews.get_question_generator_for_provider", fake_get_generator
    )
    monkeypatch.setattr(
        "app.api.interviews.build_interview_history", lambda s, d: ([], [], [])
    )

    question = generate_question_with_fallback(
        session=session,
        resume_analysis={"skills": ["SQL"]},
        db=db,
        question_strategy="fixed_independent",
        rag_builder=rag_builder,
    )

    assert question == "What is your experience with B-Trees?"
    assert session.question_provider == "mock"
    # Verify that groq and gemini both received the rag_context before failing
    assert groq_gen.generate_question.call_args[1]["rag_context"].has_context
    assert gemini_gen.generate_question.call_args[1]["rag_context"].has_context


def test_generator_prompt_incorporates_rag_reference():
    """Verify generator builds prompt including reference material from rag_context."""
    from unittest.mock import MagicMock

    from app.services.groq_question_generator import GroqQuestionGenerator

    chunk = _make_dummy_chunk(1, topic="operating_systems", title="Virtual Memory")
    rag_ctx = QuestionRAGContext(
        query="paging", topic="operating_systems", chunks=[chunk]
    )

    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "How does the MMU handle page tables?"
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    generator = GroqQuestionGenerator.__new__(GroqQuestionGenerator)
    generator.client = mock_client

    question = generator.generate_question(
        resume_analysis={"skills": ["C++"]},
        interview_type="technical",
        difficulty="hard",
        question_number=2,
        current_topic="Virtual Memory",
        rag_context=rag_ctx,
    )

    assert question == "How does the MMU handle page tables?"
    # Verify that client was called with messages containing the reference material
    prompt_sent = mock_client.chat.completions.create.call_args[1]["messages"][1][
        "content"
    ]
    assert "Reference Technical Material" in prompt_sent
    assert "Virtual Memory" in prompt_sent
