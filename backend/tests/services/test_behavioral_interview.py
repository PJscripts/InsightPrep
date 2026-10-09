"""Unit tests for HR/behavioural interview question generation and STAR evaluation."""

import json
from unittest.mock import MagicMock

from app.services.behavioral_utils import is_behavioral_context
from app.services.gemini_answer_evaluator import GeminiAnswerEvaluator
from app.services.gemini_question_generator import GeminiQuestionGenerator
from app.services.groq_answer_evaluator import GroqAnswerEvaluator
from app.services.groq_question_generator import GroqQuestionGenerator
from app.services.mock_answer_evaluator import MockAnswerEvaluator
from app.services.mock_question_generator import MockQuestionGenerator
from app.services.rag.answer_context_builder import AnswerRAGContextBuilder
from app.services.rag.question_context_builder import QuestionRAGContextBuilder
from app.services.rag.retrieval_types import RetrievalResult, RetrievedChunk

# ============================================================================
# 1. Behavioural Context Detection Tests
# ============================================================================


def test_behavioral_context_detection_hr_interview():
    """HR interviews are strictly identified as behavioral contexts."""
    assert is_behavioral_context("hr") is True
    assert is_behavioral_context("HR") is True
    assert is_behavioral_context("hr", current_topic="leadership") is True
    assert is_behavioral_context("hr", current_topic="python") is True


def test_behavioral_context_detection_technical_interview():
    """Technical interviews are strictly non-behavioral."""
    assert is_behavioral_context("technical") is False
    assert is_behavioral_context("TECHNICAL") is False
    assert is_behavioral_context("technical", current_topic="teamwork") is False
    assert is_behavioral_context("technical", current_topic="dsa") is False


def test_behavioral_context_detection_mixed_interview():
    """Mixed interviews distinguish behavioral from technical topics."""
    # Behavioral topics / questions in mixed interviews
    assert (
        is_behavioral_context("mixed", current_topic="teamwork and collaboration")
        is True
    )
    assert is_behavioral_context("mixed", current_topic="conflict resolution") is True
    assert is_behavioral_context("mixed", current_topic="leadership") is True
    assert is_behavioral_context("mixed", current_topic="career goals") is True
    assert (
        is_behavioral_context(
            "mixed",
            current_topic="general",
            question_text="Tell me about a time you handled a difficult deadline.",
        )
        is True
    )

    # Technical topics in mixed interviews
    assert is_behavioral_context("mixed", current_topic="dsa") is False
    assert is_behavioral_context("mixed", current_topic="sql databases") is False
    assert is_behavioral_context("mixed", current_topic="operating systems") is False
    assert is_behavioral_context("mixed", current_topic="concurrency") is False


# ============================================================================
# 2. Mock Question Generator Tests
# ============================================================================


def test_mock_question_generator_behavioral_strategies():
    """Mock generator produces STAR-framed questions for HR interviews."""
    generator = MockQuestionGenerator()
    resume_analysis = {"skills": ["Communication", "Leadership"]}

    # Adaptive initial question
    q_initial = generator.generate_question(
        resume_analysis=resume_analysis,
        interview_type="hr",
        difficulty="medium",
        question_number=1,
        question_strategy="adaptive_initial",
    )
    assert "introduce yourself" in q_initial.lower()
    assert "teamwork" in q_initial.lower() or "communication" in q_initial.lower()

    # Follow-up question probes action and result
    q_followup = generator.generate_question(
        resume_analysis=resume_analysis,
        interview_type="hr",
        difficulty="medium",
        question_number=2,
        current_topic="conflict resolution",
        question_strategy="follow_up",
    )
    assert "conflict resolution" in q_followup
    assert "action" in q_followup.lower()
    assert "result" in q_followup.lower() or "outcome" in q_followup.lower()

    # Topic shift asks for past experience with STAR structure
    q_shift = generator.generate_question(
        resume_analysis=resume_analysis,
        interview_type="hr",
        difficulty="medium",
        question_number=3,
        current_topic="teamwork",
        question_strategy="topic_shift",
    )
    assert "tell me about a time" in q_shift.lower()
    assert "teamwork" in q_shift
    assert "situation" in q_shift.lower()
    assert "result" in q_shift.lower()

    # Independent question
    q_indep = generator.generate_question(
        resume_analysis=resume_analysis,
        interview_type="hr",
        difficulty="hard",
        question_number=4,
        current_topic="leadership",
        question_strategy="fixed_independent",
    )
    assert "leadership" in q_indep
    assert "situation" in q_indep.lower()
    assert "actions" in q_indep.lower()


def test_mock_question_generator_preserves_technical():
    """Mock generator preserves technical questions for technical interviews."""
    generator = MockQuestionGenerator()
    resume_analysis = {"skills": ["PostgreSQL"]}

    q_tech = generator.generate_question(
        resume_analysis=resume_analysis,
        interview_type="technical",
        difficulty="medium",
        question_number=1,
        current_topic="indexing",
        question_strategy="fixed_independent",
    )
    assert "What is your experience with indexing?" in q_tech


# ============================================================================
# 3. Mock Answer Evaluator Tests
# ============================================================================


def test_mock_evaluator_complete_star_answer():
    """Mock evaluator gives high scores for complete STAR answers with agency."""
    evaluator = MockAnswerEvaluator()
    question = "Tell me about a time you led a challenging project."
    answer = (
        "When I was a lead developer at Acme Corp, our team faced a tight "
        "3-week deadline. The task was to migrate our legacy authentication service "
        "without downtime. I decided to break down the tasks into daily milestones, "
        "I organized daily standups, and I implemented an automated fallback "
        "mechanism myself. As a result, we delivered the migration 2 days ahead of "
        "schedule, improved uptime by 15%, and achieved zero customer escalations."
    )

    result = evaluator.evaluate(
        question=question,
        answer=answer,
        resume_analysis={},
        interview_type="hr",
        current_topic="leadership",
    )

    assert result["score"] >= 8.0
    assert "Strong STAR response" in result["feedback"]
    assert "dimensions" in result
    for dim in ("technical_knowledge", "problem_solving", "communication", "clarity"):
        assert dim in result["dimensions"]
        assert 0.0 <= result["dimensions"][dim] <= 10.0


def test_mock_evaluator_missing_star_components():
    """Mock evaluator identifies missing components and gives actionable feedback."""
    evaluator = MockAnswerEvaluator()
    question = "Tell me about a time you resolved a conflict."
    # Missing personal action and measurable result (vague generalities)
    answer = (
        "In our previous project, there was a disagreement about which framework "
        "to use. The task was to decide on the architecture before the sprint started."
    )

    result = evaluator.evaluate(
        question=question,
        answer=answer,
        resume_analysis={},
        interview_type="hr",
        current_topic="conflict resolution",
    )

    assert result["score"] < 7.0
    assert (
        "lacks" in result["feedback"].lower() or "missing" in result["feedback"].lower()
    )
    # Feedback points out what to strengthen
    assert (
        "personal actions" in result["feedback"].lower()
        or "outcome" in result["feedback"].lower()
    )


def test_mock_evaluator_too_brief_or_hypothetical():
    """Mock evaluator rejects superficial, overly brief, or non-STAR answers."""
    evaluator = MockAnswerEvaluator()
    result = evaluator.evaluate(
        question="Describe a failure.",
        answer="I never fail at anything.",
        resume_analysis={},
        interview_type="hr",
        current_topic="failure",
    )
    assert result["score"] <= 4.0
    assert "STAR" in result["feedback"]


# ============================================================================
# 4. Groq & Gemini Question Generator Tests
# ============================================================================


def test_groq_question_generator_behavioral_prompt():
    """GroqQuestionGenerator injects behavioral persona and STAR guidelines."""
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = (
        "Tell me about a time you resolved a conflict with a peer."
    )
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    generator = GroqQuestionGenerator.__new__(GroqQuestionGenerator)
    generator.client = mock_client

    question = generator.generate_question(
        resume_analysis={"skills": ["Collaboration", "Agile"]},
        interview_type="hr",
        difficulty="medium",
        question_number=1,
        current_topic="conflict resolution",
        question_strategy="topic_shift",
    )

    assert question == "Tell me about a time you resolved a conflict with a peer."
    call_args = mock_client.chat.completions.create.call_args[1]
    prompt = call_args["messages"][1]["content"]

    # Verify behavioral / STAR instructions are present
    assert "expert HR and behavioural interviewer" in prompt
    assert "STAR" in prompt
    assert "conflict resolution" in prompt


def test_gemini_question_generator_behavioral_prompt():
    """GeminiQuestionGenerator injects behavioral persona and STAR guidelines."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = (
        "Describe a situation where you had to lead a team through a crisis."
    )
    mock_client.models.generate_content.return_value = mock_response

    generator = GeminiQuestionGenerator.__new__(GeminiQuestionGenerator)
    generator.client = mock_client

    question = generator.generate_question(
        resume_analysis={"skills": ["Leadership"]},
        interview_type="hr",
        difficulty="hard",
        question_number=2,
        current_topic="leadership",
        question_strategy="fixed_independent",
    )

    assert (
        question
        == "Describe a situation where you had to lead a team through a crisis."
    )
    call_args = mock_client.models.generate_content.call_args[1]
    prompt = call_args["contents"]

    assert "expert HR and behavioural interviewer" in prompt
    assert "STAR" in prompt
    assert "leadership" in prompt


# ============================================================================
# 5. Groq & Gemini Answer Evaluator Tests
# ============================================================================


def test_groq_answer_evaluator_behavioral_rubric():
    """GroqAnswerEvaluator evaluates answers against the STAR behavioral rubric."""
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(
        {
            "score": 8.5,
            "feedback": (
                "Strong STAR answer with clear personal ownership and measurable "
                "outcome."
            ),
            "dimensions": {
                "technical_knowledge": 8.5,
                "problem_solving": 9.0,
                "communication": 8.0,
                "clarity": 8.5,
            },
        }
    )
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    evaluator = GroqAnswerEvaluator.__new__(GroqAnswerEvaluator)
    evaluator.client = mock_client

    result = evaluator.evaluate(
        question="Tell me about a time you handled a difficult stakeholder.",
        answer="In my previous company, a client requested scope changes late...",
        resume_analysis={},
        interview_type="hr",
        current_topic="communication",
    )

    assert result["score"] == 8.5
    assert result["dimensions"]["problem_solving"] == 9.0
    assert result["dimensions"]["technical_knowledge"] == 8.5

    # Check prompt passed to Groq
    call_args = mock_client.chat.completions.create.call_args[1]
    prompt = call_args["messages"][1]["content"]
    system_role = call_args["messages"][0]["content"]

    assert "STAR" in prompt
    assert "Ownership & Agency" in prompt
    assert "Result & Impact" in prompt
    assert "expert HR and behavioural interview evaluator" in system_role


def test_gemini_answer_evaluator_behavioral_rubric():
    """GeminiAnswerEvaluator evaluates answers against the STAR behavioral rubric."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps(
        {
            "score": 7.5,
            "feedback": (
                "Good situation and task description, but outcome could be "
                "quantified."
            ),
            "dimensions": {
                "technical_knowledge": 7.0,
                "problem_solving": 8.0,
                "communication": 7.5,
                "clarity": 7.5,
            },
        }
    )
    mock_client.models.generate_content.return_value = mock_response

    evaluator = GeminiAnswerEvaluator.__new__(GeminiAnswerEvaluator)
    evaluator.client = mock_client

    result = evaluator.evaluate(
        question="Tell me about a time you failed.",
        answer="During an early project, I underestimated the integration time...",
        resume_analysis={},
        interview_type="hr",
        current_topic="failure",
    )

    assert result["score"] == 7.5
    assert result["dimensions"]["communication"] == 7.5

    call_args = mock_client.models.generate_content.call_args[1]
    prompt = call_args["contents"]

    assert "STAR" in prompt
    assert "Ownership & Agency" in prompt
    assert "Result & Impact" in prompt
    assert "expert HR and behavioural interview evaluator" in prompt


# ============================================================================
# 6. Fallback Behavior Tests
# ============================================================================


def test_answer_evaluation_fallback_order_preserves_hr_context(monkeypatch):
    """Verify evaluation fallback order (Groq -> Gemini -> Mock) passes HR context."""
    from app.api.interviews import evaluate_answer_with_fallback

    session = MagicMock()
    session.id = 456
    session.interview_type = "hr"
    session.current_topic = "teamwork"
    session.current_question = 1
    session.evaluation_provider = "groq"

    groq_eval = MagicMock()
    groq_eval.evaluate.side_effect = RuntimeError("Groq unavailable")

    gemini_eval = MagicMock()
    gemini_eval.evaluate.side_effect = RuntimeError("Gemini quota exceeded")

    mock_eval = MagicMock()
    mock_eval.evaluate.return_value = {
        "score": 8.0,
        "feedback": "Evaluated by mock.",
        "dimensions": {
            "technical_knowledge": 8.0,
            "problem_solving": 8.0,
            "communication": 8.0,
            "clarity": 8.0,
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
        question_text="Tell me about a team conflict you resolved.",
        answer_text="I organized a retrospective and we reached a compromise.",
        resume_analysis={},
    )

    assert evaluation["score"] == 8.0
    assert session.evaluation_provider == "mock"

    # Verify all evaluators received interview_type and current_topic
    assert groq_eval.evaluate.call_args[1]["interview_type"] == "hr"
    assert groq_eval.evaluate.call_args[1]["current_topic"] == "teamwork"

    assert gemini_eval.evaluate.call_args[1]["interview_type"] == "hr"
    assert gemini_eval.evaluate.call_args[1]["current_topic"] == "teamwork"

    assert mock_eval.evaluate.call_args[1]["interview_type"] == "hr"
    assert mock_eval.evaluate.call_args[1]["current_topic"] == "teamwork"


# ============================================================================
# 7. RAG Isolation & Regression Tests
# ============================================================================


def test_rag_isolation_hr_vs_technical():
    """Verify HR interviews strictly bypass RAG while technical interviews use RAG."""
    mock_retriever = MagicMock()
    chunk = RetrievedChunk(
        chunk_id=1,
        document_id=1,
        chunk_index=0,
        chunk_text="ACID transactions ensure database reliability.",
        cosine_distance=0.2,
        similarity_score=0.8,
        source_key="dbms",
        title="ACID",
        topic="dbms",
        source_path="dbms.md",
    )
    mock_retriever.retrieve.return_value = RetrievalResult.success(
        query="dbms",
        chunks=[chunk],
    )

    # 1. Question builder
    q_builder = QuestionRAGContextBuilder(retrieval_service=mock_retriever)
    hr_q_ctx = q_builder.build_context(
        interview_type="hr",
        current_topic="teamwork",
        difficulty="medium",
    )
    assert hr_q_ctx is None
    assert not mock_retriever.retrieve.called

    tech_q_ctx = q_builder.build_context(
        interview_type="technical",
        current_topic="dbms",
        difficulty="medium",
    )
    assert tech_q_ctx is not None
    assert tech_q_ctx.has_context
    assert mock_retriever.retrieve.called

    # Reset mock retriever for answer builder
    mock_retriever.reset_mock()

    # 2. Answer builder
    a_builder = AnswerRAGContextBuilder(retrieval_service=mock_retriever)
    hr_a_ctx = a_builder.build_context(
        interview_type="hr",
        question="Tell me about a team conflict.",
        answer="I facilitated a discussion.",
        current_topic="teamwork",
    )
    assert hr_a_ctx is None
    assert not mock_retriever.retrieve.called

    tech_a_ctx = a_builder.build_context(
        interview_type="technical",
        question="What are ACID properties?",
        answer="Atomicity, Consistency, Isolation, Durability.",
        current_topic="dbms",
    )
    assert tech_a_ctx is not None
    assert tech_a_ctx.has_context
    assert mock_retriever.retrieve.called
