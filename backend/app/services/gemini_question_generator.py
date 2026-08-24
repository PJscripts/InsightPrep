from typing import Any

from google import genai

from app.core.settings import settings
from app.services.question_generator import QuestionGenerator


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
    ) -> str:
        skills = resume_analysis.get("skills", [])
        strengths = resume_analysis.get("strengths", [])
        skill_gaps = resume_analysis.get("skill_gaps", [])
        recommended_topics = resume_analysis.get("recommended_topics", [])

        prompt = f"""
You are an AI interviewer generating one personalized interview question.

Candidate profile:
Skills: {skills}
Strengths: {strengths}
Skill gaps: {skill_gaps}
Recommended topics: {recommended_topics}

Interview settings:
Type: {interview_type}
Difficulty: {difficulty}
Question number: {question_number}

Generate exactly ONE interview question.

Requirements:
- Personalize it using the candidate profile.
- Match the requested interview type and difficulty.
- Focus on skills, projects, experience, or identified gaps.
- Do not invent candidate experience.
- Do not include the answer.
- Do not include numbering.
- Return ONLY the question text.
"""

        try:
            response = self.client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
            )
        except Exception as exc:
            raise RuntimeError("Gemini question generation failed") from exc

        question = (response.text or "").strip()

        if not question:
            raise RuntimeError("Gemini returned an empty question")

        return question


gemini_question_generator: QuestionGenerator | None = None

if settings.llm_mode.lower() == "gemini":
    gemini_question_generator = GeminiQuestionGenerator()
