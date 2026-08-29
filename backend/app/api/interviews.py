from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
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
from app.services.gemini_answer_evaluator import GeminiAnswerEvaluator
from app.services.gemini_question_generator import GeminiQuestionGenerator
from app.services.groq_answer_evaluator import GroqAnswerEvaluator
from app.services.groq_question_generator import GroqQuestionGenerator
from app.services.mock_answer_evaluator import MockAnswerEvaluator
from app.services.mock_question_generator import MockQuestionGenerator

router = APIRouter(prefix="/interviews", tags=["Interviews"])


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


def build_interview_history(
    session: InterviewSession,
    db: Session,
) -> tuple[
    list[str],
    list[str],
    list[dict[str, Any]],
]:
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

    return (
        previous_questions,
        previous_answers,
        previous_evaluations,
    )


def generate_question_with_fallback(
    session: InterviewSession,
    resume_analysis: dict[str, Any],
    db: Session,
) -> str:
    (
        previous_questions,
        previous_answers,
        previous_evaluations,
    ) = build_interview_history(session, db)

    provider = session.question_provider.lower()

    if provider == "mock":
        generator = get_question_generator_for_provider("mock")

        return generator.generate_question(
            resume_analysis=resume_analysis,
            interview_type=session.interview_type,
            difficulty=session.difficulty,
            question_number=session.current_question,
            previous_questions=previous_questions,
            previous_answers=previous_answers,
            previous_evaluations=previous_evaluations,
        )

    try:
        generator = get_question_generator_for_provider(provider)

        return generator.generate_question(
            resume_analysis=resume_analysis,
            interview_type=session.interview_type,
            difficulty=session.difficulty,
            question_number=session.current_question,
            previous_questions=previous_questions,
            previous_answers=previous_answers,
            previous_evaluations=previous_evaluations,
        )

    except Exception:
        if provider == "gemini":
            fallback_provider = settings.question_fallback_llm.lower()
        else:
            fallback_provider = "mock"

        if fallback_provider == "groq":
            try:
                generator = get_question_generator_for_provider("groq")

                question_text = generator.generate_question(
                    resume_analysis=resume_analysis,
                    interview_type=session.interview_type,
                    difficulty=session.difficulty,
                    question_number=session.current_question,
                    previous_questions=previous_questions,
                    previous_answers=previous_answers,
                    previous_evaluations=previous_evaluations,
                )

                session.question_provider = "groq"
                db.flush()

                return question_text

            except Exception:
                pass

        generator = get_question_generator_for_provider(
            settings.llm_final_fallback.lower(),
        )

        question_text = generator.generate_question(
            resume_analysis=resume_analysis,
            interview_type=session.interview_type,
            difficulty=session.difficulty,
            question_number=session.current_question,
            previous_questions=previous_questions,
            previous_answers=previous_answers,
            previous_evaluations=previous_evaluations,
        )

        session.question_provider = settings.llm_final_fallback.lower()
        db.flush()

        return question_text


def evaluate_answer_with_fallback(
    session: InterviewSession,
    question_text: str,
    answer_text: str,
    resume_analysis: dict[str, Any],
) -> dict[str, Any]:
    provider = session.evaluation_provider.lower()

    if provider == "mock":
        evaluator = get_answer_evaluator_for_provider("mock")

        return evaluator.evaluate(
            question=question_text,
            answer=answer_text,
            resume_analysis=resume_analysis,
        )

    try:
        evaluator = get_answer_evaluator_for_provider(provider)

        return evaluator.evaluate(
            question=question_text,
            answer=answer_text,
            resume_analysis=resume_analysis,
        )

    except Exception:
        if provider == "gemini":
            fallback_provider = settings.evaluation_fallback_llm.lower()
        else:
            fallback_provider = "mock"

        if fallback_provider == "groq":
            try:
                evaluator = get_answer_evaluator_for_provider("groq")

                evaluation = evaluator.evaluate(
                    question=question_text,
                    answer=answer_text,
                    resume_analysis=resume_analysis,
                )

                session.evaluation_provider = "groq"

                return evaluation

            except Exception:
                pass

        evaluator = get_answer_evaluator_for_provider(
            settings.llm_final_fallback.lower(),
        )

        evaluation = evaluator.evaluate(
            question=question_text,
            answer=answer_text,
            resume_analysis=resume_analysis,
        )

        session.evaluation_provider = settings.llm_final_fallback.lower()

        return evaluation


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
            detail=("Please upload and analyze a resume before starting an interview"),
        )

    session = InterviewSession(
        user_id=current_user.id,
        resume_id=latest_resume.id,
        interview_type=config.interview_type,
        difficulty=config.difficulty,
        total_questions=config.total_questions,
        current_question=1,
        status="in_progress",
        question_provider=settings.question_primary_llm.lower(),
        evaluation_provider=settings.evaluation_primary_llm.lower(),
    )

    db.add(session)
    db.flush()

    try:
        question_text = generate_question_with_fallback(
            session=session,
            resume_analysis=latest_resume.analysis or {},
            db=db,
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

    db.add(question)
    db.commit()
    db.refresh(session)

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
        "question_text": question.question_text,
        "question_type": question.question_type,
        "status": session.status,
    }


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

    answer = InterviewAnswer(
        question_id=current_question.id,
        answer_text=data.answer_text,
        score=evaluation["score"],
        feedback=evaluation["feedback"],
    )

    db.add(answer)

    if session.current_question >= session.total_questions:
        session.status = "completed"
        db.commit()

        return {
            "session_id": session.id,
            "status": "completed",
            "message": "Interview completed",
            "evaluation": evaluation,
        }

    session.current_question += 1

    try:
        next_question_text = generate_question_with_fallback(
            session=session,
            resume_analysis=resume.analysis or {},
            db=db,
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

    db.add(next_question)
    db.commit()

    return {
        "session_id": session.id,
        "status": "in_progress",
        "current_question": session.current_question,
        "total_questions": session.total_questions,
        "evaluation": evaluation,
        "question": {
            "id": next_question.id,
            "question_number": next_question.question_number,
            "question_text": next_question.question_text,
            "question_type": next_question.question_type,
        },
    }


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

    return {
        "session_id": session.id,
        "status": session.status,
        "total_questions": session.total_questions,
        "answered_questions": len(scores),
        "overall_score": overall_score,
        "performance": performance,
        "results": [
            {
                "question_number": question.question_number,
                "question": question.question_text,
                "answer": (question.answer.answer_text if question.answer else None),
                "score": (question.answer.score if question.answer else None),
                "feedback": (question.answer.feedback if question.answer else None),
            }
            for question in questions
        ],
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
    db.commit()

    return {
        "session_id": session.id,
        "status": session.status,
        "message": "Interview session abandoned",
    }
