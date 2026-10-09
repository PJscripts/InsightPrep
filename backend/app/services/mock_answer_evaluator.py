from typing import Any

from app.services.answer_evaluator import AnswerEvaluator
from app.services.rag.answer_context import AnswerRAGContext


class MockAnswerEvaluator:
    def evaluate(
        self,
        question: str,
        answer: str,
        resume_analysis: dict[str, Any],
        rag_context: AnswerRAGContext | None = None,
        interview_type: str = "technical",
        current_topic: str | None = None,
    ) -> dict[str, Any]:
        from app.services.behavioral_utils import is_behavioral_context

        is_behavioral = is_behavioral_context(
            interview_type=interview_type,
            current_topic=current_topic,
            question_text=question,
        )

        answer_text = answer.strip()
        answer_length = len(answer_text)
        lower_ans = answer_text.lower()

        if is_behavioral:
            # Check for STAR presence and substance (not merely buzzwords)
            has_situation = any(
                w in lower_ans
                for w in [
                    "when",
                    "situation",
                    "project",
                    "time",
                    "team",
                    "company",
                    "client",
                ]
            )
            has_task = any(
                w in lower_ans
                for w in [
                    "task",
                    "goal",
                    "challenge",
                    "problem",
                    "deadline",
                    "objective",
                    "needed to",
                ]
            )
            has_action = any(
                w in lower_ans
                for w in [
                    "i decided",
                    "i took",
                    "i organized",
                    "i led",
                    "i implemented",
                    "i spoke",
                    "i resolved",
                    "i worked",
                    "my role",
                    "my approach",
                ]
            )
            has_result = any(
                w in lower_ans
                for w in [
                    "result",
                    "outcome",
                    "impact",
                    "achieved",
                    "improved",
                    "learned",
                    "delivered",
                    "%",
                    "increased",
                    "reduced",
                ]
            )

            # Evaluate substance & ownership vs vague/hypothetical
            star_count = sum([has_situation, has_task, has_action, has_result])

            missing_elements = []
            if not has_situation:
                missing_elements.append("clear context or situation")
            if not has_task:
                missing_elements.append("the specific task/challenge")
            if not has_action:
                missing_elements.append(
                    "individual actions and ownership (what you personally did)"
                )
            if not has_result:
                missing_elements.append("tangible results or measurable outcome")

            if answer_length < 35 or star_count == 0:
                score = 3.5
                feedback = (
                    "The response is too brief or hypothetical. Structure your "
                    "answer using the STAR method: clearly describe the Situation, "
                    "Task, your specific Action, and the Result."
                )
            elif star_count <= 2:
                score = 5.5
                missing_str = ", ".join(missing_elements)
                feedback = (
                    f"Good start describing past experience, but the answer lacks "
                    f"{missing_str}. Strengthen your response by detailing your "
                    "personal actions and quantifying the final outcome."
                )
            elif star_count == 3:
                score = 7.5
                missing_str = ", ".join(missing_elements)
                feedback = (
                    "Solid behavioral example with clear context and ownership. "
                    "To make it exceptional, address the missing element: "
                    f"{missing_str}."
                )
            else:
                score = 8.5
                feedback = (
                    "Strong STAR response. You effectively articulated the "
                    "situation, the task, your individual actions, and the "
                    "measurable results with good self-awareness."
                )

            return {
                "score": score,
                "feedback": feedback,
                "dimensions": {
                    "technical_knowledge": score,
                    "problem_solving": min(
                        10.0, score + 0.3 if has_action and has_result else score
                    ),
                    "communication": max(
                        0.0, score - 0.2 if answer_length < 80 else score + 0.2
                    ),
                    "clarity": score,
                },
            }

        # Technical interview rubric
        if answer_length < 30:
            score = 4.0
            feedback = (
                "The answer is too brief. Add more explanation, reasoning, "
                "and a concrete example."
            )
        elif answer_length < 100:
            score = 6.5
            feedback = (
                "The answer addresses the question, but it would benefit "
                "from more depth and specific examples."
            )
        else:
            score = 8.0
            feedback = (
                "The answer provides reasonable detail and demonstrates a "
                "good understanding of the topic."
            )

        return {
            "score": score,
            "feedback": feedback,
            "dimensions": {
                "technical_knowledge": score,
                "problem_solving": min(10.0, score + 0.2),
                "communication": max(0.0, score - 0.2),
                "clarity": score,
            },
        }


mock_answer_evaluator: AnswerEvaluator = MockAnswerEvaluator()
