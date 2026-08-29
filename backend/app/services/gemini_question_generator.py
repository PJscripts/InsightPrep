from typing import Any

from google import genai

from app.core.settings import settings


class GeminiQuestionGenerator:
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not configured")

        self.client = genai.Client(
            api_key=settings.gemini_api_key,
        )

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
You are an expert technical interviewer conducting a personalized
interview.

Candidate profile:
Skills: {resume_analysis.get("skills", [])}
Experience: {resume_analysis.get("experience", [])}
Education: {resume_analysis.get("education", [])}
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
- Maintain a consistent professional interview style.
- Maintain the requested difficulty.
- Do not repeat any previous question.
- Build naturally on the candidate's previous answers.
- Use the candidate profile for personalization.
- Consider previous evaluations when deciding what to ask next.
- Probe weak areas when appropriate.
- Avoid asking about something the candidate has already demonstrated
  sufficiently unless a deeper follow-up is useful.
- Do not invent candidate experience or skills.
- Return ONLY the question text.
"""

        try:
            response = self.client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
            )
        except Exception as exc:
            raise RuntimeError(
                "Gemini question generation failed",
            ) from exc

        question = (response.text or "").strip()

        if not question:
            raise RuntimeError(
                "Gemini returned an empty interview question",
            )

        return question
