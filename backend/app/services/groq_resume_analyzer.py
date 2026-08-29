import json
from typing import Any

from groq import Groq

from app.core.settings import settings


class GroqResumeAnalyzer:
    def __init__(self) -> None:
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is not configured")

        self.client = Groq(api_key=settings.groq_api_key)

    def analyze(self, resume_text: str) -> dict[str, Any]:
        resume_text = resume_text[:20000]

        prompt = f"""
Analyze the following resume for an interview preparation platform.

Return ONLY valid JSON with exactly these keys:
- skills
- experience
- education
- projects
- strengths
- skill_gaps
- recommended_topics

Rules:
- skills: list of technical skills explicitly supported by the resume
- experience: concise list of relevant experience items
- education: concise list of education items
- projects: concise list of relevant projects
- strengths: 2-5 evidence-based strengths
- skill_gaps: 2-5 likely gaps or areas that need stronger evidence
- recommended_topics: 3-7 interview preparation topics
- Do not invent facts that are not supported by the resume.

Resume:
{resume_text}
"""

        try:
            response = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert resume analyst for "
                            "technical interview preparation."
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
                "Groq resume analysis failed",
            ) from exc

        text = (response.choices[0].message.content or "").strip()

        if not text:
            raise RuntimeError(
                "Groq returned an empty resume analysis",
            )

        try:
            result = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Groq returned invalid resume analysis JSON",
            ) from exc

        return result
