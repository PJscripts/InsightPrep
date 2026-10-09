import json
from typing import Any

from google import genai

from app.core.settings import settings
from app.services.evaluation_dimensions import (
    normalize_skill_dimensions,
)


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
        rag_context: Any | None = None,
        interview_type: str = "technical",
        current_topic: str | None = None,
    ) -> dict[str, Any]:
        from app.services.behavioral_utils import is_behavioral_context

        skills = resume_analysis.get("skills", [])
        strengths = resume_analysis.get("strengths", [])
        skill_gaps = resume_analysis.get("skill_gaps", [])

        rag_section = ""
        if rag_context and hasattr(rag_context, "format_for_prompt"):
            formatted = rag_context.format_for_prompt()
            if formatted:
                rag_section = f"\n{formatted}\n"

        is_behavioral = is_behavioral_context(
            interview_type=interview_type,
            current_topic=current_topic,
            question_text=question,
        )

        if is_behavioral:
            persona = (
                "You are an expert HR and behavioural interview evaluator "
                "specializing in competency-based assessment and the STAR framework "
                "(Situation, Task, Action, Result)."
            )
            rubric_section = """
Scoring rubric for Behavioural / STAR assessment:

0-2:
Irrelevant, evasive, or demonstrates no concrete experience.
No Situation, Task, Action, or Result.

3-4:
Extremely vague or hypothetical answer. Missing critical STAR components
(e.g., no personal action taken, no tangible result, or unclear situation).
Speaks only in generic team generalities without personal ownership.

5-6:
Describes a relevant situation and task, but actions lack specificity or
personal ownership, or the result/impact is missing or unquantified.

7-8:
Clear and structured past-experience example covering Situation, Task,
specific personal Actions taken, and the Result/outcome. Demonstrates
ownership, decision-making, and self-awareness with minor gaps in impact
or reflection.

9-10:
Exemplary STAR response: compelling context, well-defined task, highly
specific proactive actions and decision-making rationale, and measurable,
impactful results with thoughtful reflection on lessons learned.

Behavioural evaluation criteria:
1. STAR Structure & Completeness (Situation, Task, Action, Result)
2. Personal Ownership & Agency
   (Focus on individual contributions and decisions vs generic "we")
3. Decision-Making & Problem-Solving
   (Rationale behind choices, navigating constraints or conflict)
4. Result & Impact (Measurable outcome, business/team impact, learning reflection)
5. Actionable Feedback
   (Highlight strengths and clearly identify missing or weak STAR elements)
- Do not reward answers merely for being long or containing superficial STAR
  buzzwords without genuine substance.

Score these four skill dimensions independently from 0 to 10:
- technical_knowledge: role & domain competency (understanding of role responsibilities,
  realistic workplace context, and relevant domain practices)
- problem_solving: conflict resolution, critical thinking, initiative, and
  decision-making under constraints
- communication: narrative flow, conciseness, structured articulation, and
  listening comprehension
- clarity: specificity of actions, concrete details vs vague generalities, and
  measurable results
"""
        else:
            persona = "You are an expert interviewer evaluating one candidate answer."
            rubric_section = """
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

Also score these four skill dimensions independently from 0 to 10:
- technical_knowledge: demonstrated technical understanding
- problem_solving: reasoning, decomposition, and approach
- communication: how clearly the answer is expressed
- clarity: structure, precision, and ease of understanding
"""

        prompt = f"""
{persona}

Candidate profile:
Skills: {skills}
Strengths: {strengths}
Skill gaps: {skill_gaps}

Interview type: {interview_type}
Interview question:
{question}

Candidate answer:
{answer}
{rag_section}
Evaluate ONLY the answer given to this question.

{rubric_section}

Important rules:
- Score only what the candidate actually demonstrated.
- Do not give credit for skills merely because they appear on the resume.
- Do not invent experience, projects, or knowledge.
- Explain both strengths and weaknesses in the feedback.
- Give practical improvement advice.
- The feedback should be concise but useful to the candidate.

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
        dimensions = normalize_skill_dimensions(result.get("dimensions"))

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
        if dimensions is None:
            raise RuntimeError("Gemini evaluation dimensions are invalid")

        return {
            "score": round(score, 1),
            "feedback": feedback.strip(),
            "dimensions": dimensions,
        }
