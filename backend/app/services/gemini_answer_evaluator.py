import json
from typing import Any

from google import genai

from app.core.settings import settings


class GeminiAnswerEvaluator:
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not configured")

        self.client = genai.Client(
            api_key=settings.gemini_api_key,
        )

    def evaluate(
        self,
        question: str,
        answer: str,
        resume_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        skills = resume_analysis.get("skills", [])
        strengths = resume_analysis.get("strengths", [])
        skill_gaps = resume_analysis.get("skill_gaps", [])

        prompt = f"""
You are an expert interviewer evaluating one candidate answer.

Candidate profile:
Skills: {skills}
Strengths: {strengths}
Skill gaps: {skill_gaps}

Interview question:
{question}

Candidate answer:
{answer}

Evaluate ONLY the answer given to this question.

Scoring rubric:
0-2:
The answer is incorrect, irrelevant, extremely incomplete,
or shows almost no understanding.

3-4:
The answer shows limited understanding but contains major gaps,
incorrect reasoning, or insufficient explanation.

5-6:
The answer is partially correct and relevant but lacks depth,
specific examples, or important technical details.

7-8:
The answer is mostly correct, relevant, clear, and technically
sound, with reasonable depth and minor gaps.

9-10:
The answer is highly accurate, complete, technically strong,
well-structured, and demonstrates strong reasoning.

Evaluation criteria:
1. Correctness
2. Relevance to the question
3. Technical depth
4. Clarity
5. Completeness

Important rules:
- Score only what the candidate actually demonstrated.
- Do not give credit for skills merely because they appear on the resume.
- Do not invent experience, projects, or knowledge.
- A short but correct answer may score moderately well,
  but should not receive a high score without sufficient depth.
- Explain both strengths and weaknesses in the feedback.
- Give practical improvement advice.
- The feedback should be concise but useful to the candidate.

Return ONLY valid JSON:
{{
  "score": 0.0,
  "feedback": "..."
}}

Additional requirements:
- score must be a number from 0.0 to 10.0.
- Use one decimal place.
- feedback must be a non-empty string.
- Do not include markdown.
- Do not include any additional JSON fields.
"""

        try:
            response = self.client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
            )
        except Exception as exc:
            raise RuntimeError(
                "Gemini answer evaluation failed",
            ) from exc

        text = (response.text or "").strip()

        if not text:
            raise RuntimeError(
                "Gemini returned an empty evaluation",
            )

        return self._parse_evaluation(text)

    @staticmethod
    def _parse_evaluation(text: str) -> dict[str, Any]:
        try:
            result = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Gemini returned invalid evaluation JSON",
            ) from exc

        score = result.get("score")
        feedback = result.get("feedback")

        if not isinstance(score, (int, float)):
            raise RuntimeError(
                "Gemini evaluation score is invalid",
            )

        if not isinstance(feedback, str) or not feedback.strip():
            raise RuntimeError(
                "Gemini evaluation feedback is invalid",
            )

        score = float(score)

        if not 0 <= score <= 10:
            raise RuntimeError(
                "Gemini evaluation score is outside 0-10",
            )

        return {
            "score": round(score, 1),
            "feedback": feedback.strip(),
        }
