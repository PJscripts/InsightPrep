from typing import Any

from app.services.question_generator import QuestionGenerator


class MockQuestionGenerator:
    def generate_question(
        self,
        resume_analysis: dict[str, Any],
        interview_type: str,
        difficulty: str,
        question_number: int,
    ) -> str:
        skills = resume_analysis.get("skills", [])
        gaps = resume_analysis.get("skill_gaps", [])

        primary_skill = skills[0] if skills else "software development"
        gap_topic = gaps[0] if gaps else "system design"

        questions = [
            (
                f"Explain your experience with {primary_skill} and describe "
                "a project where you used it."
            ),
            (
                f"How would you approach a {difficulty} {interview_type} "
                f"problem involving {primary_skill}?"
            ),
            (
                f"What are the important considerations when working with "
                f"{primary_skill} in a production application?"
            ),
            (f"How would you improve your knowledge of {gap_topic} for an interview?"),
            (
                f"Describe a technical challenge you faced while working "
                f"with {primary_skill} and how you solved it."
            ),
        ]

        return questions[(question_number - 1) % len(questions)]


mock_question_generator: QuestionGenerator = MockQuestionGenerator()
