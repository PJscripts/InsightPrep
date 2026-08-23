import json
from typing import Any

from google import genai

from app.core.settings import settings


class GeminiResumeAnalyzer:
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not configured")

        self.client = genai.Client(
            api_key=settings.gemini_api_key,
        )

    def analyze(self, resume_text: str) -> dict[str, Any]:
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
- Do not invent facts that are not supported by the resume

Resume:
{resume_text}
"""

        response = self.client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )

        return json.loads(response.text)
