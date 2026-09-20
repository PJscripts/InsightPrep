from typing import Literal

from pydantic import BaseModel, Field


class InterviewConfig(BaseModel):
    interview_mode: Literal["fixed", "adaptive"] = "fixed"
    interview_type: Literal["technical", "hr", "mixed"] = "technical"
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    total_questions: Literal[3, 5, 10] | None = 10

    @classmethod
    def validate_total_questions(cls, value):
        return value


class InterviewSessionResponse(BaseModel):
    id: int
    resume_id: int | None
    interview_mode: str
    interview_type: str
    difficulty: str
    total_questions: int | None
    current_question: int
    status: str


class AnswerSubmission(BaseModel):
    answer_text: str = Field(min_length=1, max_length=5000)
