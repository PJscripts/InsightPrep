import logging
import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.settings import settings
from app.models.interview_answer import InterviewAnswer
from app.models.interview_question import InterviewQuestion
from app.models.interview_session import InterviewSession
from app.models.resume import Resume
from app.models.user import User
from app.schemas.interview import (
    AnswerSubmission,
    InterviewConfig,
    InterviewSessionResponse,
)
from app.services.answer_evaluator import AnswerEvaluator
from app.services.elevenlabs_tts import text_to_speech
from app.services.evaluation_dimensions import (
    SKILL_DIMENSIONS,
    normalize_skill_dimensions,
)
from app.services.gemini_answer_evaluator import GeminiAnswerEvaluator
from app.services.gemini_question_generator import GeminiQuestionGenerator
from app.services.groq_answer_evaluator import GroqAnswerEvaluator
from app.services.groq_question_generator import GroqQuestionGenerator
from app.services.mock_answer_evaluator import MockAnswerEvaluator
from app.services.mock_question_generator import MockQuestionGenerator
from app.services.rag.answer_context_builder import AnswerRAGContextBuilder
from app.services.rag.question_context_builder import QuestionRAGContextBuilder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interviews", tags=["Interviews"])

ADAPTIVE_MIN_QUESTIONS = 8
ADAPTIVE_MAX_QUESTIONS = 15
ADAPTIVE_MIN_TOPICS = 3
FOLLOW_UP_SCORE_THRESHOLD = 7.0
SHORT_ANSWER_LENGTH = 120


def get_question_generator_for_provider(provider: str):
    provider = provider.lower()

    if provider == "gemini":
        return GeminiQuestionGenerator()

    if provider == "groq":
        return GroqQuestionGenerator()

    if provider == "mock":
        return MockQuestionGenerator()

    raise ValueError(f"Unsupported question provider: {provider}")


def get_answer_evaluator_for_provider(provider: str) -> AnswerEvaluator:
    provider = provider.lower()

    if provider == "gemini":
        return GeminiAnswerEvaluator()

    if provider == "groq":
        return GroqAnswerEvaluator()

    if provider == "mock":
        return MockAnswerEvaluator()

    raise ValueError(f"Unsupported evaluation provider: {provider}")


def _as_text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    result: list[str] = []
    for item in value:
        if isinstance(item, dict):
            text = item.get("title") or item.get("name") or item.get("description")
            if text:
                result.append(str(text).strip())
        elif item is not None:
            text = str(item).strip()
            if text:
                result.append(text)

    return result


def get_candidate_topics(
    resume_analysis: dict[str, Any], interview_type: str
) -> list[str]:
    sources = [
        ("recommended_topics", resume_analysis.get("recommended_topics", [])),
        ("skills", resume_analysis.get("skills", [])),
        ("projects", resume_analysis.get("projects", [])),
        ("experience", resume_analysis.get("experience", [])),
    ]

    topics: list[str] = []
    seen: set[str] = set()

    for _, values in sources:
        for topic in _as_text_list(values):
            key = topic.casefold()
            if key not in seen:
                seen.add(key)
                topics.append(topic)

    if interview_type in {"hr", "mixed"}:
        generic_topics = [
            "motivation and career goals",
            "teamwork and collaboration",
            "problem solving",
            "communication",
        ]
        for topic in generic_topics:
            key = topic.casefold()
            if key not in seen:
                seen.add(key)
                topics.append(topic)

    if interview_type in {"technical", "mixed"}:
        generic_topics = [
            "problem solving",
            "software design",
            "testing and debugging",
        ]
        for topic in generic_topics:
            key = topic.casefold()
            if key not in seen:
                seen.add(key)
                topics.append(topic)

    return topics


def initialize_session_topics(
    session: InterviewSession,
    resume_analysis: dict[str, Any],
) -> str:
    if session.interview_mode == "adaptive":
        session.current_topic = "Introduction"
        session.topic_question_count = 1
        session.covered_topics = ["Introduction"]
        return "adaptive_initial"

    topics = get_candidate_topics(resume_analysis, session.interview_type)
    first_topic = topics[0] if topics else "core knowledge"

    session.current_topic = first_topic
    session.topic_question_count = 1
    session.covered_topics = [first_topic]

    return "fixed_independent"


def build_interview_history(
    session: InterviewSession,
    db: Session,
) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    questions = db.scalars(
        select(InterviewQuestion)
        .where(InterviewQuestion.session_id == session.id)
        .order_by(InterviewQuestion.question_number)
    ).all()

    previous_questions = [question.question_text for question in questions]

    previous_answers = [
        question.answer.answer_text
        for question in questions
        if question.answer is not None
    ]

    previous_evaluations = [
        {
            "score": question.answer.score,
            "feedback": question.answer.feedback,
        }
        for question in questions
        if question.answer is not None
    ]

    return previous_questions, previous_answers, previous_evaluations


def get_question_rag_builder() -> QuestionRAGContextBuilder:
    """Return QuestionRAGContextBuilder for technical question generation."""
    try:
        from app.core.settings import settings
        from app.services.rag.embeddings import (
            LocalSentenceTransformerEmbeddingProvider,
        )
        from app.services.rag.retrieval_service import VectorRetrievalService

        rag_db_url = getattr(settings, "rag_database_url", None)
        if not rag_db_url:
            # If no explicit RAG database URL configured, RAG remains disabled
            return QuestionRAGContextBuilder(retrieval_service=None)

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        rag_engine = create_engine(rag_db_url, pool_pre_ping=True)
        rag_session_factory = sessionmaker(
            bind=rag_engine, autoflush=False, autocommit=False
        )
        embedding_provider = LocalSentenceTransformerEmbeddingProvider(
            enabled=True, dimensions=384
        )
        retrieval_service = VectorRetrievalService(
            session_factory=rag_session_factory,
            embedding_provider=embedding_provider,
            default_top_k=3,
        )
        return QuestionRAGContextBuilder(retrieval_service=retrieval_service)
    except Exception as exc:
        logger.warning(
            "Failed to initialize RAG retrieval service for questions: %s", exc
        )
        return QuestionRAGContextBuilder(retrieval_service=None)


def generate_question_with_fallback(
    session: InterviewSession,
    resume_analysis: dict[str, Any],
    db: Session,
    question_strategy: str,
    rag_builder: QuestionRAGContextBuilder | None = None,
) -> str:
    (
        previous_questions,
        previous_answers,
        previous_evaluations,
    ) = build_interview_history(session, db)

    # Resolve RAG context for technical interviews fail-open
    rag_context = None
    try:
        builder = rag_builder or get_question_rag_builder()
        rag_context = builder.build_context(
            interview_type=session.interview_type,
            current_topic=session.current_topic,
            difficulty=session.difficulty,
            question_strategy=question_strategy,
            previous_questions=previous_questions,
            resume_analysis=resume_analysis,
        )
    except Exception as exc:
        logger.warning(
            "RAG context retrieval failed open for session_id=%s: %s",
            session.id,
            exc,
        )

    kwargs = {
        "resume_analysis": resume_analysis,
        "interview_type": session.interview_type,
        "difficulty": session.difficulty,
        "question_number": session.current_question,
        "previous_questions": previous_questions,
        "previous_answers": previous_answers,
        "previous_evaluations": previous_evaluations,
        "question_strategy": question_strategy,
        "current_topic": session.current_topic,
        "covered_topics": list(session.covered_topics or []),
        "rag_context": rag_context,
    }

    provider = session.question_provider.lower()

    if provider == "mock":
        return get_question_generator_for_provider("mock").generate_question(**kwargs)

    try:
        generator = get_question_generator_for_provider(provider)
        question_text = generator.generate_question(**kwargs)
        logger.info(
            "Interview question generated: session_id=%s provider=%s "
            "question=%s rag_grounded=%s",
            session.id,
            provider,
            session.current_question,
            rag_context is not None and rag_context.has_context,
        )
        return question_text
    except Exception:
        fallback_provider = settings.question_fallback_llm.lower()
        logger.warning(
            "Question provider failed: session_id=%s provider=%s fallback=%s",
            session.id,
            provider,
            fallback_provider,
        )

        if fallback_provider != "mock":
            try:
                question_text = get_question_generator_for_provider(
                    fallback_provider
                ).generate_question(**kwargs)
                session.question_provider = fallback_provider
                db.flush()
                logger.info(
                    "Question provider fallback succeeded: session_id=%s provider=%s "
                    "question=%s",
                    session.id,
                    fallback_provider,
                    session.current_question,
                )
                return question_text
            except Exception:
                logger.warning(
                    "Question fallback provider failed: session_id=%s provider=%s",
                    session.id,
                    fallback_provider,
                )

        final_fallback = settings.llm_final_fallback.lower()
        generator = get_question_generator_for_provider(final_fallback)
        question_text = generator.generate_question(**kwargs)
        session.question_provider = final_fallback
        db.flush()
        logger.warning(
            "Question final fallback used: session_id=%s provider=%s question=%s",
            session.id,
            final_fallback,
            session.current_question,
        )
        return question_text


def get_answer_rag_builder() -> AnswerRAGContextBuilder:
    """Return AnswerRAGContextBuilder for technical answer evaluation."""
    try:
        from app.core.settings import settings
        from app.services.rag.embeddings import (
            LocalSentenceTransformerEmbeddingProvider,
        )
        from app.services.rag.retrieval_service import VectorRetrievalService

        rag_db_url = getattr(settings, "rag_database_url", None)
        if not rag_db_url:
            return AnswerRAGContextBuilder(retrieval_service=None)

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        rag_engine = create_engine(rag_db_url, pool_pre_ping=True)
        rag_session_factory = sessionmaker(
            bind=rag_engine, autoflush=False, autocommit=False
        )
        embedding_provider = LocalSentenceTransformerEmbeddingProvider(
            enabled=True, dimensions=384
        )
        retrieval_service = VectorRetrievalService(
            session_factory=rag_session_factory,
            embedding_provider=embedding_provider,
            default_top_k=3,
        )
        return AnswerRAGContextBuilder(retrieval_service=retrieval_service)
    except Exception as exc:
        logger.warning(
            "Failed to initialize RAG retrieval service for answer evaluation: %s",
            exc,
        )
        return AnswerRAGContextBuilder(retrieval_service=None)


def evaluate_answer_with_fallback(
    session: InterviewSession,
    question_text: str,
    answer_text: str,
    resume_analysis: dict[str, Any],
    rag_builder: AnswerRAGContextBuilder | None = None,
) -> dict[str, Any]:
    # Resolve RAG context for technical interviews fail-open
    rag_context = None
    try:
        builder = rag_builder or get_answer_rag_builder()
        rag_context = builder.build_context(
            interview_type=session.interview_type,
            question=question_text,
            answer=answer_text,
            current_topic=session.current_topic,
            resume_analysis=resume_analysis,
        )
    except Exception as exc:
        logger.warning(
            "RAG evaluation context retrieval failed open for session_id=%s: %s",
            session.id,
            exc,
        )

    provider = session.evaluation_provider.lower()

    eval_kwargs = {
        "question": question_text,
        "answer": answer_text,
        "resume_analysis": resume_analysis,
        "rag_context": rag_context,
        "interview_type": session.interview_type,
        "current_topic": session.current_topic,
    }

    if provider == "mock":
        evaluation = get_answer_evaluator_for_provider("mock").evaluate(**eval_kwargs)
        evaluation["dimensions"] = normalize_skill_dimensions(
            evaluation.get("dimensions")
        )
        return evaluation

    try:
        evaluator = get_answer_evaluator_for_provider(provider)
        evaluation = evaluator.evaluate(**eval_kwargs)
        logger.info(
            "Interview answer evaluated: session_id=%s provider=%s "
            "question=%s rag_grounded=%s",
            session.id,
            provider,
            session.current_question,
            rag_context is not None and rag_context.has_context,
        )
        dimensions = normalize_skill_dimensions(evaluation.get("dimensions"))
        if dimensions is None:
            raise RuntimeError("Evaluation provider returned invalid skill dimensions")
        evaluation["dimensions"] = dimensions
        return evaluation
    except Exception:
        fallback_provider = settings.evaluation_fallback_llm.lower()
        logger.warning(
            "Evaluation provider failed: session_id=%s provider=%s fallback=%s "
            "question=%s",
            session.id,
            provider,
            fallback_provider,
            session.current_question,
        )

        if fallback_provider != "mock":
            try:
                evaluation = get_answer_evaluator_for_provider(
                    fallback_provider
                ).evaluate(**eval_kwargs)
                session.evaluation_provider = fallback_provider
                logger.info(
                    "Evaluation provider fallback succeeded: session_id=%s "
                    "provider=%s question=%s",
                    session.id,
                    fallback_provider,
                    session.current_question,
                )
                dimensions = normalize_skill_dimensions(evaluation.get("dimensions"))
                if dimensions is None:
                    raise RuntimeError(
                        "Evaluation fallback provider returned invalid skill dimensions"
                    )
                evaluation["dimensions"] = dimensions
                return evaluation
            except Exception:
                logger.warning(
                    "Evaluation fallback provider failed: session_id=%s provider=%s "
                    "question=%s",
                    session.id,
                    fallback_provider,
                    session.current_question,
                )

        final_fallback = settings.llm_final_fallback.lower()
        evaluator = get_answer_evaluator_for_provider(final_fallback)
        evaluation = evaluator.evaluate(**eval_kwargs)
        session.evaluation_provider = final_fallback
        logger.warning(
            "Evaluation final fallback used: session_id=%s provider=%s question=%s",
            session.id,
            final_fallback,
            session.current_question,
        )
        dimensions = normalize_skill_dimensions(evaluation.get("dimensions"))
        if dimensions is None:
            raise RuntimeError(
                "Final evaluation fallback returned invalid skill dimensions"
            )
        evaluation["dimensions"] = dimensions
        return evaluation


def normalize_feedback(feedback: Any) -> str:
    if isinstance(feedback, list):
        raw_points = [str(item).strip() for item in feedback if str(item).strip()]
    else:
        raw_text = str(feedback or "").strip()
        raw_points = [line.strip() for line in raw_text.splitlines() if line.strip()]

    if not raw_points:
        return "- No detailed feedback was returned."

    points: list[str] = []
    for point in raw_points:
        point = re.sub(r"^[-*•]\s*", "", point).strip()
        if point and point not in points:
            points.append(point)

    return "\n".join(f"- {point}" for point in points[:6])


def choose_next_topic(
    session: InterviewSession,
    resume_analysis: dict[str, Any],
) -> str:
    topics = get_candidate_topics(resume_analysis, session.interview_type)
    used = {topic.casefold() for topic in (session.covered_topics or [])}

    for topic in topics:
        if topic.casefold() not in used:
            return topic

    return f"additional {session.interview_type} topic"


def should_end_adaptive(
    session: InterviewSession,
    score: float,
) -> bool:
    answered = session.current_question
    covered_topic_count = len(session.covered_topics or [])

    if answered >= ADAPTIVE_MAX_QUESTIONS:
        return True

    if answered < ADAPTIVE_MIN_QUESTIONS:
        return False

    if (
        covered_topic_count >= ADAPTIVE_MIN_TOPICS
        and session.topic_question_count >= 2
        and score >= FOLLOW_UP_SCORE_THRESHOLD
    ):
        return True

    if answered >= 10 and covered_topic_count >= 4:
        return True

    return False


def plan_next_question(
    session: InterviewSession,
    answer_text: str,
    score: float,
    resume_analysis: dict[str, Any],
) -> str:
    is_fixed_short = session.interview_mode == "fixed" and session.total_questions in {
        3,
        5,
    }

    if session.interview_mode == "adaptive":
        if session.topic_question_count < 2 or (
            session.topic_question_count < 3
            and (
                score < FOLLOW_UP_SCORE_THRESHOLD
                or len(answer_text.strip()) < SHORT_ANSWER_LENGTH
            )
        ):
            session.topic_question_count += 1
            return "follow_up"

    elif not is_fixed_short and session.total_questions == 10:
        if session.topic_question_count < 2 or (
            session.topic_question_count < 3
            and (
                score < FOLLOW_UP_SCORE_THRESHOLD
                or len(answer_text.strip()) < SHORT_ANSWER_LENGTH
            )
        ):
            session.topic_question_count += 1
            return "follow_up"

    next_topic = choose_next_topic(session, resume_analysis)
    session.current_topic = next_topic
    session.topic_question_count = 1

    covered = list(session.covered_topics or [])
    if next_topic.casefold() not in {topic.casefold() for topic in covered}:
        covered.append(next_topic)
    session.covered_topics = covered

    return "topic_shift"


def aggregate_skill_profile(
    questions: list[InterviewQuestion],
) -> dict[str, float] | None:
    totals = {key: 0.0 for key in SKILL_DIMENSIONS}
    counts = {key: 0 for key in SKILL_DIMENSIONS}

    for question in questions:
        answer = question.answer
        if answer is None or not answer.skill_dimensions:
            continue
        dimensions = normalize_skill_dimensions(answer.skill_dimensions)
        if dimensions is None:
            continue
        for key in SKILL_DIMENSIONS:
            totals[key] += dimensions[key]
            counts[key] += 1

    if not any(counts.values()):
        return None

    return {
        key: round(totals[key] / counts[key], 2)
        for key in SKILL_DIMENSIONS
        if counts[key] > 0
    }


def build_final_feedback(
    scores: list[float], questions: list[InterviewQuestion]
) -> list[str]:
    if not scores:
        return ["No evaluated answers were available."]

    overall_score = round(sum(scores) / len(scores), 2)
    feedback_points = [
        (
            f"Overall performance was {overall_score}/10 across "
            f"{len(scores)} evaluated answers."
        )
    ]

    strong_count = sum(score >= 8 for score in scores)
    weak_count = sum(score < 6 for score in scores)

    if strong_count:
        feedback_points.append(
            f"You demonstrated strong performance on {strong_count} question(s)."
        )

    if weak_count:
        feedback_points.append(
            f"{weak_count} question(s) need additional improvement or "
            "deeper explanation."
        )

    improvement_points: list[str] = []
    low_score_questions = sorted(
        (
            question
            for question in questions
            if question.answer is not None
            and question.answer.score is not None
            and question.answer.score < 7
        ),
        key=lambda question: question.answer.score,
    )

    for question in low_score_questions:
        if question.answer is None:
            continue

        for point in normalize_feedback(question.answer.feedback).splitlines():
            clean_point = re.sub(r"^-\s*", "", point).strip()
            if clean_point and clean_point not in improvement_points:
                improvement_points.append(clean_point)

        if len(improvement_points) >= 3:
            break

    for point in improvement_points[:3]:
        feedback_points.append(point)

    if len(feedback_points) == 1:
        feedback_points.append(
            "Continue practicing concise, technically accurate answers "
            "with clear reasoning and examples."
        )

    return feedback_points[:6]


@router.post(
    "/sessions",
    response_model=InterviewSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_interview_session(
    config: InterviewConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    latest_resume = db.scalar(
        select(Resume)
        .where(
            Resume.user_id == current_user.id,
            Resume.analysis_status == "analyzed",
        )
        .order_by(Resume.created_at.desc())
    )

    if latest_resume is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload and analyze a resume before starting an interview",
        )

    session = InterviewSession(
        user_id=current_user.id,
        resume_id=latest_resume.id,
        interview_type=config.interview_type,
        difficulty=config.difficulty,
        total_questions=config.total_questions,
        current_question=1,
        status="in_progress",
        interview_mode=config.interview_mode,
        question_provider=settings.question_primary_llm.lower(),
        evaluation_provider=settings.evaluation_primary_llm.lower(),
    )

    initial_strategy = initialize_session_topics(
        session,
        latest_resume.analysis or {},
    )

    db.add(session)
    db.flush()

    logger.info(
        "Interview session started: session_id=%s mode=%s type=%s "
        "difficulty=%s total_questions=%s",
        session.id,
        session.interview_mode,
        session.interview_type,
        session.difficulty,
        session.total_questions,
    )

    try:
        question_text = generate_question_with_fallback(
            session=session,
            resume_analysis=latest_resume.analysis or {},
            db=db,
            question_strategy=initial_strategy,
        )
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to generate the first interview question",
        )

    question = InterviewQuestion(
        session_id=session.id,
        question_number=1,
        question_text=question_text,
        question_type=config.interview_type,
    )

    try:
        db.add(question)
        db.commit()
        db.refresh(session)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save the interview session",
        ) from exc

    return session


@router.get("/sessions/{session_id}/current")
def get_current_question(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.scalar(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == current_user.id,
        )
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found",
        )

    if session.status in {"completed", "abandoned"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview session is no longer active",
        )

    question = db.scalar(
        select(InterviewQuestion).where(
            InterviewQuestion.session_id == session.id,
            InterviewQuestion.question_number == session.current_question,
        )
    )

    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Current interview question not found",
        )

    return {
        "session_id": session.id,
        "question_number": question.question_number,
        "total_questions": session.total_questions,
        "interview_mode": session.interview_mode,
        "interview_type": session.interview_type,
        "current_topic": session.current_topic,
        "question_text": question.question_text,
        "question_type": question.question_type,
        "status": session.status,
    }


@router.get("/sessions/{session_id}/question/audio")
def get_current_question_audio(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.scalar(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == current_user.id,
        )
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found",
        )

    if session.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview session is not active",
        )

    question = db.scalar(
        select(InterviewQuestion).where(
            InterviewQuestion.session_id == session.id,
            InterviewQuestion.question_number == session.current_question,
        )
    )

    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Current interview question not found",
        )

    try:
        audio = text_to_speech.synthesize(question.question_text)
    except Exception as exc:
        logger.warning(
            "Question TTS failed: session_id=%s question=%s error=%s",
            session.id,
            session.current_question,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Question voice playback is currently unavailable",
        ) from exc

    return Response(content=audio, media_type="audio/mpeg")


@router.post("/sessions/{session_id}/answer")
def submit_answer(
    session_id: int,
    data: AnswerSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.scalar(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == current_user.id,
        )
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found",
        )

    if session.status in {"completed", "abandoned"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview session is no longer active",
        )

    current_question = db.scalar(
        select(InterviewQuestion).where(
            InterviewQuestion.session_id == session.id,
            InterviewQuestion.question_number == session.current_question,
        )
    )

    if current_question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Current interview question not found",
        )

    existing_answer = db.scalar(
        select(InterviewAnswer).where(
            InterviewAnswer.question_id == current_question.id,
        )
    )

    if existing_answer is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This question has already been answered",
        )

    resume = db.get(Resume, session.resume_id)

    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume associated with interview not found",
        )

    evaluation = evaluate_answer_with_fallback(
        session=session,
        question_text=current_question.question_text,
        answer_text=data.answer_text,
        resume_analysis=resume.analysis or {},
    )
    evaluation["feedback"] = normalize_feedback(evaluation.get("feedback"))

    answer = InterviewAnswer(
        question_id=current_question.id,
        answer_text=data.answer_text,
        score=evaluation["score"],
        feedback=evaluation["feedback"],
        skill_dimensions=evaluation.get("dimensions"),
    )
    db.add(answer)

    if session.interview_mode == "fixed":
        if session.current_question >= (session.total_questions or 0):
            session.status = "completed"

            try:
                db.commit()
            except Exception as exc:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Could not save the completed interview",
                ) from exc

            logger.info(
                "Interview session completed: session_id=%s mode=fixed questions=%s",
                session.id,
                session.current_question,
            )

            return {
                "session_id": session.id,
                "status": "completed",
                "message": "Interview completed",
            }
    else:
        if should_end_adaptive(session, float(evaluation["score"])):
            session.status = "completed"

            try:
                db.commit()
            except Exception as exc:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Could not save the completed adaptive interview",
                ) from exc

            logger.info(
                "Interview session completed: session_id=%s mode=adaptive questions=%s",
                session.id,
                session.current_question,
            )

            return {
                "session_id": session.id,
                "status": "completed",
                "message": "Adaptive interview completed",
            }

    session.current_question += 1

    question_strategy = plan_next_question(
        session=session,
        answer_text=data.answer_text,
        score=float(evaluation["score"]),
        resume_analysis=resume.analysis or {},
    )

    try:
        next_question_text = generate_question_with_fallback(
            session=session,
            resume_analysis=resume.analysis or {},
            db=db,
            question_strategy=question_strategy,
        )
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to generate the next interview question",
        )

    next_question = InterviewQuestion(
        session_id=session.id,
        question_number=session.current_question,
        question_text=next_question_text,
        question_type=session.interview_type,
    )

    try:
        db.add(next_question)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save the next interview question",
        ) from exc

    return {
        "session_id": session.id,
        "status": "in_progress",
        "current_question": session.current_question,
        "total_questions": session.total_questions,
        "interview_mode": session.interview_mode,
        "interview_type": session.interview_type,
        "current_topic": session.current_topic,
        "question": {
            "id": next_question.id,
            "question_number": next_question.question_number,
            "question_text": next_question.question_text,
            "question_type": next_question.question_type,
        },
    }


@router.get("/history")
def get_interview_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = db.scalars(
        select(InterviewSession)
        .where(
            InterviewSession.user_id == current_user.id,
            InterviewSession.status == "completed",
        )
        .order_by(InterviewSession.created_at.desc())
    ).all()

    history = []

    for session in sessions:
        questions = db.scalars(
            select(InterviewQuestion)
            .where(InterviewQuestion.session_id == session.id)
            .order_by(InterviewQuestion.question_number)
        ).all()

        scores = [
            question.answer.score
            for question in questions
            if question.answer is not None and question.answer.score is not None
        ]
        overall_score = round(sum(scores) / len(scores), 2) if scores else None

        if overall_score is None:
            performance = "Not Available"
        elif overall_score >= 8:
            performance = "Excellent"
        elif overall_score >= 6:
            performance = "Good"
        elif overall_score >= 4:
            performance = "Needs Improvement"
        else:
            performance = "Weak"

        created_at = session.created_at
        created_at_iso = (
            created_at.isoformat() + "Z"
            if created_at is not None and created_at.tzinfo is None
            else created_at.isoformat() if created_at is not None else None
        )

        history.append(
            {
                "session_id": session.id,
                "interview_mode": session.interview_mode,
                "interview_type": session.interview_type,
                "difficulty": session.difficulty,
                "total_questions": session.total_questions,
                "answered_questions": len(scores),
                "overall_score": overall_score,
                "performance": performance,
                "created_at": created_at_iso,
            }
        )

    logger.info(
        "Interview history fetched: user_id=%s sessions=%s",
        current_user.id,
        len(history),
    )

    return {"history": history}


@router.get("/progress")
def get_interview_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = db.scalars(
        select(InterviewSession)
        .where(
            InterviewSession.user_id == current_user.id,
            InterviewSession.status == "completed",
        )
        .order_by(InterviewSession.created_at.asc())
    ).all()

    progress = []

    for session in sessions:
        questions = db.scalars(
            select(InterviewQuestion)
            .where(InterviewQuestion.session_id == session.id)
            .order_by(InterviewQuestion.question_number)
        ).all()

        scores = [
            question.answer.score
            for question in questions
            if question.answer is not None and question.answer.score is not None
        ]

        if not scores:
            continue

        created_at = session.created_at
        created_at_iso = (
            created_at.isoformat() + "Z"
            if created_at is not None and created_at.tzinfo is None
            else created_at.isoformat() if created_at is not None else None
        )

        skill_scores = aggregate_skill_profile(questions)

        progress.append(
            {
                "session_id": session.id,
                "created_at": created_at_iso,
                "overall_score": round(sum(scores) / len(scores), 2),
                "interview_mode": session.interview_mode,
                "interview_type": session.interview_type,
                "difficulty": session.difficulty,
                "answered_questions": len(scores),
                "total_questions": session.total_questions,
                "skill_scores": skill_scores,
            }
        )

    return {"progress": progress}


@router.get("/sessions/{session_id}/result")
def get_interview_result(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.scalar(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == current_user.id,
        )
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found",
        )

    if session.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview is not completed yet",
        )

    questions = db.scalars(
        select(InterviewQuestion)
        .where(InterviewQuestion.session_id == session.id)
        .order_by(InterviewQuestion.question_number)
    ).all()

    scores = [
        question.answer.score
        for question in questions
        if question.answer is not None and question.answer.score is not None
    ]

    if not scores:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No evaluated answers found",
        )

    overall_score = round(sum(scores) / len(scores), 2)

    if overall_score >= 8:
        performance = "Excellent"
    elif overall_score >= 6:
        performance = "Good"
    elif overall_score >= 4:
        performance = "Needs Improvement"
    else:
        performance = "Weak"

    results = [
        {
            "question_number": question.question_number,
            "question": question.question_text,
            "answer": question.answer.answer_text if question.answer else None,
            "score": question.answer.score if question.answer else None,
            "feedback": (
                normalize_feedback(question.answer.feedback)
                if question.answer
                else "- No feedback available."
            ),
            "topic": (
                session.current_topic
                if question.question_number == session.current_question
                else None
            ),
        }
        for question in questions
    ]

    return {
        "session_id": session.id,
        "status": session.status,
        "interview_mode": session.interview_mode,
        "interview_type": session.interview_type,
        "difficulty": session.difficulty,
        "total_questions": session.total_questions,
        "answered_questions": len(scores),
        "overall_score": overall_score,
        "performance": performance,
        "final_feedback": build_final_feedback(scores, questions),
        "skill_profile": aggregate_skill_profile(questions),
        "results": results,
    }


@router.post("/sessions/{session_id}/abandon")
def abandon_interview_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.scalar(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == current_user.id,
        )
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found",
        )

    if session.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Completed interview cannot be abandoned",
        )

    if session.status == "abandoned":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview session is already abandoned",
        )

    session.status = "abandoned"

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not abandon the interview session",
        ) from exc

    logger.info(
        "Interview session abandoned: session_id=%s current_question=%s",
        session.id,
        session.current_question,
    )

    return {
        "session_id": session.id,
        "status": session.status,
        "message": "Interview session abandoned",
    }
