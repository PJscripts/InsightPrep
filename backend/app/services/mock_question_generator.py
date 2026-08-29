from typing import Any


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
    ) -> str:
        skills = resume_analysis.get("skills", [])
        gaps = resume_analysis.get("skill_gaps", [])

        primary_skill = skills[0] if skills else "software development"
        gap_topic = gaps[0] if gaps else "system design"

        questions = [
            (
                f"Explain your experience with {primary_skill} "
                "and describe a project where you used it."
            ),
            (
                f"How would you approach a {difficulty} "
                f"{interview_type} problem involving {primary_skill}?"
            ),
            (
                f"What are the important considerations when working "
                f"with {primary_skill} in a production application?"
            ),
            (f"How would you improve your knowledge of {gap_topic} for an interview?"),
            (
                f"Describe a technical challenge you faced while "
                f"working with {primary_skill} and how you solved it."
            ),
        ]

        return questions[(question_number - 1) % len(questions)]


mock_question_generator = MockQuestionGenerator()
