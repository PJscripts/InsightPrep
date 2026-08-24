from typing import Any, Protocol


class AnswerEvaluator(Protocol):
    def evaluate(
        self,
        question: str,
        answer: str,
        resume_analysis: dict[str, Any],
    ) -> dict[str, Any]: ...
