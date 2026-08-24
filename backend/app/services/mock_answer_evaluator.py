from typing import Any

from app.services.answer_evaluator import AnswerEvaluator


class MockAnswerEvaluator:
    def evaluate(
        self,
        question: str,
        answer: str,
        resume_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        answer_length = len(answer.strip())

        if answer_length < 30:
            score = 4.0
            feedback = (
                "The answer is too brief. Add more explanation, "
                "reasoning, and a concrete example."
            )
        elif answer_length < 100:
            score = 6.5
            feedback = (
                "The answer addresses the question, but it would "
                "benefit from more depth and specific examples."
            )
        else:
            score = 8.0
            feedback = (
                "The answer provides reasonable detail and demonstrates "
                "a good understanding of the topic."
            )

        return {
            "score": score,
            "feedback": feedback,
        }


mock_answer_evaluator: AnswerEvaluator = MockAnswerEvaluator()
