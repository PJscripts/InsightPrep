from typing import Any

from app.services.behavioral_utils import is_behavioral_context
from app.services.rag.question_context import QuestionRAGContext


class MockQuestionGenerator:
    def generate_question(
        self,
        resume_analysis: dict[str, Any],
        interview_type: str,
        difficulty: str,
        question_number: int,
        previous_questions: list[str] | None = None,
        previous_answers: list[str] | None = None,
        previous_evaluations: list[dict[str, Any]] | None = None,
        question_strategy: str = "fixed_independent",
        current_topic: str | None = None,
        covered_topics: list[str] | None = None,
        rag_context: QuestionRAGContext | None = None,
    ) -> str:
        skills = resume_analysis.get("skills", [])
        primary_skill = skills[0] if skills else "software development"
        topic = current_topic or primary_skill

        is_behavioral = is_behavioral_context(
            interview_type=interview_type,
            current_topic=current_topic,
        )

        if is_behavioral:
            if question_strategy == "adaptive_initial":
                return (
                    "Could you briefly introduce yourself, highlighting a past project "
                    "where teamwork and communication were critical to your success?"
                )
            if question_strategy == "follow_up":
                return (
                    f"In that situation regarding {topic}, what specific action did "
                    "you take and what was the measurable outcome or result?"
                )
            if question_strategy == "topic_shift":
                return (
                    f"Tell me about a time when you demonstrated {topic}. "
                    "Describe the situation, your specific role/action, and the "
                    "final result."
                )
            return (
                f"Tell me about a time when you had to manage a challenge involving "
                f"{topic}. Walk me through the situation, your specific actions, "
                "and the outcome."
            )

        if question_strategy == "adaptive_initial":
            return (
                "Could you briefly introduce yourself in the context of this interview?"
            )

        if question_strategy == "follow_up":
            return f"What was your main contribution or decision related to {topic}?"

        if question_strategy == "topic_shift":
            return f"What is your experience with {topic}?"

        return f"What is your experience with {topic}?"
