import json
from typing import Any

from groq import Groq

from app.core.settings import settings
from app.services.evaluation_dimensions import (
    normalize_skill_dimensions,
)


class GroqAnswerEvaluator:
    def __init__(self) -> None:
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is not configured")

        self.client = Groq(api_key=settings.groq_api_key)

    def evaluate(
        self,
        question: str,
        answer: str,
        resume_analysis: dict[str, Any],
        rag_context: Any | None = None,
    ) -> dict[str, Any]:
        rag_section = ""
        if rag_context and hasattr(rag_context, "format_for_prompt"):
            formatted = rag_context.format_for_prompt()
            if formatted:
                rag_section = f"\n{formatted}\n"

        prompt = f"""
You are an expert technical interviewer evaluating one candidate answer.

Candidate profile:
Skills: {resume_analysis.get("skills", [])}
Experience: {resume_analysis.get("experience", [])}
Projects: {resume_analysis.get("projects", [])}
Strengths: {resume_analysis.get("strengths", [])}
Skill gaps: {resume_analysis.get("skill_gaps", [])}

Interview question:
{question}

Candidate answer:
{answer}
{rag_section}
Evaluate ONLY what the candidate actually demonstrated.

Scoring rubric:

0-2:
Incorrect, irrelevant, or demonstrates almost no understanding.

3-4:
Limited understanding with major gaps, errors, or weak reasoning.

5-6:
Partially correct and relevant but lacks depth or important details.

7-8:
Mostly correct, relevant, clear, and technically sound with minor gaps.

9-10:
Highly accurate, complete, technically strong, clear, and well reasoned.

Evaluation criteria:
1. Correctness
2. Relevance
3. Technical depth
4. Clarity
5. Completeness

Also score these four skill dimensions independently from 0 to 10:
- technical_knowledge: demonstrated technical understanding
- problem_solving: reasoning, decomposition, and approach
- communication: how clearly the answer is expressed
- clarity: structure, precision, and ease of understanding

Rules:
- Score only the submitted answer.
- Do not give credit simply because a skill appears on the resume.
- Do not invent experience or knowledge.
- Explain strengths and weaknesses.
- Give practical improvement advice.
- Use one decimal place for the score.
- Score must be between 0 and 10.

Return ONLY valid JSON:
{{
    "score": 0.0,
    "feedback": "...",
    "dimensions": {{
        "technical_knowledge": 0.0,
        "problem_solving": 0.0,
        "communication": 0.0,
        "clarity": 0.0
    }}
}}
"""

        try:
            response = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a strict but constructive technical "
                            "interview evaluator."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
        except Exception as exc:
            raise RuntimeError(
                "Groq answer evaluation failed",
            ) from exc

        text = (response.choices[0].message.content or "").strip()

        if not text:
            raise RuntimeError(
                "Groq returned an empty evaluation",
            )

        try:
            result = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Groq returned invalid evaluation JSON",
            ) from exc

        score = result.get("score")
        feedback = result.get("feedback")
        dimensions = normalize_skill_dimensions(result.get("dimensions"))

        if not isinstance(score, (int, float)):
            raise RuntimeError(
                "Groq evaluation score is invalid",
            )

        if not isinstance(feedback, str) or not feedback.strip():
            raise RuntimeError(
                "Groq evaluation feedback is invalid",
            )

        score = float(score)

        if not 0 <= score <= 10:
            raise RuntimeError(
                "Groq evaluation score is outside 0-10",
            )
        if dimensions is None:
            raise RuntimeError("Groq evaluation dimensions are invalid")

        return {
            "score": round(score, 1),
            "feedback": feedback.strip(),
            "dimensions": dimensions,
        }
