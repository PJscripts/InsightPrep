from typing import Any

from groq import Groq

from app.core.settings import settings


class GroqQuestionGenerator:
    def __init__(self) -> None:
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is not configured")

        self.client = Groq(
            api_key=settings.groq_api_key,
            timeout=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
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
Ask one concise introduction question relevant to the candidate and role.
Do not ask multiple questions in one message.
"""
        elif question_strategy == "follow_up":
            strategy = f"""
Ask exactly ONE concise follow-up about the candidate's previous answer.
Stay on the current topic: {current_topic}.
Probe one useful detail, decision, claim, weakness, or example.
Do not introduce a new topic.
Do not combine multiple questions.
"""
        elif question_strategy == "topic_shift":
            strategy = f"""
Switch to the new topic: {current_topic}.
Ask exactly ONE concise question about it.
Do not continue drilling the previous topic.
Do not combine multiple questions.
"""
        else:
            strategy = f"""
Ask exactly ONE concise independent question about: {current_topic}.
Do not make it a follow-up to the previous question.
Do not combine multiple questions.
"""

        prompt = f"""
You are a professional interviewer conducting a personalized interview.

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
- Match the requested difficulty.
- Do not repeat previous questions.
- Use the candidate profile for personalization.
- Do not invent candidate experience or skills.
- Ask one thing at a time.
- Keep the question concise.
- Return ONLY the question text.
"""
        try:
            response = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert interviewer. "
                            "Ask concise, relevant, personalized interview questions."
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
            raise RuntimeError("Groq question generation failed") from exc

        question = (response.choices[0].message.content or "").strip()
        if not question:
            raise RuntimeError("Groq returned an empty interview question")

        return question
