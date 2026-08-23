from typing import Any, Protocol


class ResumeAnalyzer(Protocol):
    def analyze(self, resume_text: str) -> dict[str, Any]: ...


def empty_analysis() -> dict[str, Any]:
    return {
        "skills": [],
        "experience": [],
        "education": [],
        "projects": [],
        "strengths": [],
        "skill_gaps": [],
        "recommended_topics": [],
    }
