from typing import Any

from groq import Groq

from app.core.settings import settings


class GroqQuestionGenerator:
    def __init__(self) -> None:
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is not configured")

        self.client = Groq(api_key=settings.groq_api_key)

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
        previous_questions = previous_questions or []
        previous_answers = previous_answers or []
        previous_evaluations = previous_evaluations or []

        prompt = f"""
You are a professional technical interviewer continuing an ongoing
interview.

Candidate profile:
Skills: {resume_analysis.get("skills", [])}
Experience: {resume_analysis.get("experience", [])}
Projects: {resume_analysis.get("projects", [])}
Strengths: {resume_analysis.get("strengths", [])}
Skill gaps: {resume_analysis.get("skill_gaps", [])}
Recommended topics: {resume_analysis.get("recommended_topics", [])}

Interview type: {interview_type}
Difficulty: {difficulty}
Current question number: {question_number}

Previous questions:
{previous_questions}

Previous candidate answers:
{previous_answers}

Previous evaluations:
{previous_evaluations}

Generate exactly ONE interview question.

Rules:
- Maintain the same interview style and difficulty.
- Do not repeat a previous question.
- Build naturally on the candidate's previous answers.
- Use the candidate profile to personalize the question.
- Prefer useful follow-up questions when appropriate.
- Do not invent candidate experience or skills.
- The question should be appropriate for the current question number.
- Return ONLY the question text.
"""

        try:
            response = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert technical interviewer. "
                            "Ask clear, relevant, personalized interview questions."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.3,
            )
        except Exception as exc:
            raise RuntimeError(
                "Groq question generation failed",
            ) from exc

        question = (response.choices[0].message.content or "").strip()

        if not question:
            raise RuntimeError(
                "Groq returned an empty interview question",
            )

        return question
