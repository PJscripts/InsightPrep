from typing import Any

from google import genai
from google.genai import types

from app.core.settings import settings


class GeminiQuestionGenerator:
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not configured")

        self.client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options=types.HttpOptions(
                timeout=int(settings.llm_timeout_seconds * 1000),
                retry_options=types.HttpRetryOptions(
                    attempts=settings.llm_max_retries + 1,
                    initial_delay=0.25,
                    max_delay=0.5,
                    exp_base=2.0,
                    jitter=0.0,
                    http_status_codes=[408, 429, 500, 502, 503, 504],
                ),
            ),
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
        question_strategy: str = "fixed_independent",
        current_topic: str | None = None,
        covered_topics: list[str] | None = None,
    ) -> str:
        previous_questions = previous_questions or []
        previous_answers = previous_answers or []
        previous_evaluations = previous_evaluations or []
        covered_topics = covered_topics or []

        if question_strategy == "adaptive_initial":
            strategy = """
This is the opening question of an adaptive interview.
Ask one concise introduction question that helps the candidate introduce
their background in a way relevant to this interview.
Do not ask multiple questions in one message.
Do not ask for a full life story.
"""
        elif question_strategy == "follow_up":
            strategy = f"""
Ask exactly ONE concise follow-up question based on the candidate's previous
answer. Stay focused on the current topic: {current_topic}.
Probe one useful detail, decision, claim, weakness, or example from the answer.
Do not introduce a new topic.
Do not combine multiple questions.
"""
        elif question_strategy == "topic_shift":
            strategy = f"""
Move to the new topic: {current_topic}.
Ask exactly ONE concise question about that topic.
Do not continue drilling the previous topic.
Do not combine multiple questions.
"""
        else:
            strategy = f"""
Ask exactly ONE concise independent question about the current topic:
{current_topic}.
Do not make it a follow-up to the previous question.
Do not combine multiple questions.
"""

        prompt = f"""
You are an expert interviewer conducting a personalized interview.

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
Current topic: {current_topic}
Topics already covered: {covered_topics}

Previous questions:
{previous_questions}

Previous candidate answers:
{previous_answers}

Previous evaluations:
{previous_evaluations}

Question strategy:
{strategy}

General rules:
- Maintain a professional interview style.
- Match the requested difficulty.
- Do not repeat previous questions.
- Use the candidate profile for personalization.
- Do not invent candidate experience or skills.
- Return ONLY the question text.
- Keep the question concise.
- Ask one thing at a time.
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
            raise RuntimeError("Gemini returned an empty interview question")

        return question
