import json
from typing import Any

from google import genai
from google.genai import types

from app.core.settings import settings


class GeminiResumeAnalyzer:
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not configured")

        self.client = genai.Client(
            api_key=settings.gemini_api_key,
        )

    def analyze(self, resume_text: str) -> dict[str, Any]:
        resume_text = resume_text[:20000]

        prompt = f"""
Analyze the following resume for an interview preparation platform.

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

        schema = {
            "type": "OBJECT",
            "properties": {
                "skills": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                },
                "experience": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                },
                "education": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                },
                "projects": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                },
                "strengths": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                },
                "skill_gaps": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                },
                "recommended_topics": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                },
            },
            "required": [
                "skills",
                "experience",
                "education",
                "projects",
                "strengths",
                "skill_gaps",
                "recommended_topics",
            ],
        }

        try:
            response = self.client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )
        except Exception as exc:
            raise RuntimeError("Gemini resume analysis failed") from exc

        text = (response.text or "").strip()

        if not text:
            raise RuntimeError(
                "Gemini returned an empty resume analysis",
            )

        try:
            result = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Gemini returned invalid resume analysis JSON",
            ) from exc

        return result
