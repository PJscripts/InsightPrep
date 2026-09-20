from typing import Any

SKILL_DIMENSIONS = (
    "technical_knowledge",
    "problem_solving",
    "communication",
    "clarity",
)


def normalize_skill_dimensions(value: Any) -> dict[str, float] | None:
    if not isinstance(value, dict):
        return None

    normalized: dict[str, float] = {}
    for key in SKILL_DIMENSIONS:
        raw = value.get(key)
        if not isinstance(raw, (int, float)):
            return None
        score = float(raw)
        if not 0 <= score <= 10:
            return None
        normalized[key] = round(score, 1)

    return normalized
