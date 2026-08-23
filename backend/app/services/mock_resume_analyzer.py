from typing import Any

from app.services.resume_analyzer import ResumeAnalyzer, empty_analysis


class MockResumeAnalyzer:
    def analyze(self, resume_text: str) -> dict[str, Any]:
        analysis = empty_analysis()
        text = resume_text.lower()

        skill_keywords = {
            "Python": "python",
            "Java": "java",
            "C++": "c++",
            "JavaScript": "javascript",
            "SQL": "sql",
            "React": "react",
            "FastAPI": "fastapi",
            "PostgreSQL": "postgresql",
            "Docker": "docker",
            "Git": "git",
        }

        analysis["skills"] = [
            skill for skill, keyword in skill_keywords.items() if keyword in text
        ]

        if "project" in text:
            analysis["projects"].append("Resume contains project experience.")

        if "bachelor" in text or "b.tech" in text:
            analysis["education"].append("Bachelor-level education detected.")

        if "experience" in text or "intern" in text:
            analysis["experience"].append(
                "Professional or project experience detected."
            )

        if len(analysis["skills"]) >= 5:
            analysis["strengths"].append("Strong technical skill coverage.")
        else:
            analysis["strengths"].append("Technical skill base identified.")

        common_topics = {
            "System Design": "system design",
            "Testing": "testing",
            "REST APIs": "rest",
            "Data Structures": "data structures",
            "Databases": "database",
        }

        analysis["skill_gaps"] = [
            topic for topic, keyword in common_topics.items() if keyword not in text
        ][:3]

        analysis["recommended_topics"] = [
            "Data Structures",
            "DBMS",
            "REST APIs",
        ]

        return analysis


mock_analyzer: ResumeAnalyzer = MockResumeAnalyzer()
