"""Utilities and definitions for behavioral / HR interview classification
and prompts.
"""

# Standard HR/behavioral domains and keywords
HR_TOPIC_KEYWORDS = {
    "teamwork",
    "collaboration",
    "conflict",
    "conflict resolution",
    "leadership",
    "failure",
    "mistake",
    "decision-making",
    "decision making",
    "achievement",
    "accomplishment",
    "motivation",
    "career goals",
    "communication",
    "adaptability",
    "work ethic",
    "pressure",
    "time management",
    "prioritization",
    "interpersonal",
    "problem solving",
    "ownership",
    "initiative",
    "culture",
    "mentorship",
}

# Technical keywords indicating technical topic even if phrasing contains common words
TECHNICAL_TOPIC_KEYWORDS = {
    "dsa",
    "data structures",
    "algorithms",
    "sql",
    "dbms",
    "database",
    "databases",
    "operating systems",
    "operating system",
    "virtual memory",
    "paging",
    "concurrency",
    "threads",
    "deadlock",
    "networking",
    "networks",
    "computer networks",
    "tcp",
    "udp",
    "http",
    "dns",
    "osi",
    "python",
    "javascript",
    "react",
    "backend",
    "frontend",
    "api",
    "rest",
    "docker",
    "kubernetes",
    "system design",
    "software design",
    "testing and debugging",
    "git",
    "ci/cd",
    "c++",
    "java",
    "golang",
    "microservices",
}


def is_behavioral_context(
    interview_type: str | None,
    current_topic: str | None = None,
    question_text: str | None = None,
) -> bool:
    """Determine whether current question/eval should use the behavioral (HR) framework.

    - If interview_type is 'hr', returns True unless explicitly overridden.
    - If interview_type is 'technical', returns False.
    - If interview_type is 'mixed':
      - Evaluates current_topic and question_text against behavioral vs technical
        markers.
    """
    clean_type = (interview_type or "").strip().lower()
    if clean_type == "hr":
        return True
    if clean_type == "technical":
        return False

    # For mixed or unspecified, check topic and question content
    topic_str = (current_topic or "").strip().lower()
    q_str = (question_text or "").strip().lower()

    combined = f"{topic_str} {q_str}"

    # Check for direct behavioral indicators
    behavioral_markers = [
        "tell me about a time",
        "describe a situation",
        "give an example of",
        "have you ever faced",
        "how did you handle a",
        "how do you handle conflict",
        "disagreement with a team",
        "leadership",
        "teamwork",
        "conflict resolution",
        "career goals",
        "motivation",
        "failure",
    ]
    for marker in behavioral_markers:
        if marker in combined:
            return True

    # If topic matches an HR keyword and does not match a technical keyword
    for hr_kw in HR_TOPIC_KEYWORDS:
        if hr_kw in topic_str:
            # Verify it's not a technical topic with similar words
            # (e.g., "technical problem solving")
            is_explicit_tech = any(
                tech_kw in topic_str for tech_kw in TECHNICAL_TOPIC_KEYWORDS
            )
            if not is_explicit_tech:
                return True

    return False


STAR_GUIDANCE_TEXT = (
    "In HR and behavioural interviews, structured answers using the STAR method "
    "(Situation, Task, Action, Result) help communicate past experience clearly. "
    "Focus on your specific role and decisions."
)
