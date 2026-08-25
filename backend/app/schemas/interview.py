from typing import Literal

from pydantic import BaseModel, Field


class InterviewConfig(BaseModel):
    interview_type: Literal["technical", "hr", "mixed"] = "technical"
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    total_questions: Literal[5, 10] = 10


class InterviewSessionResponse(BaseModel):
    id: int
    resume_id: int | None
    interview_type: str
    difficulty: str
    total_questions: int
    current_question: int
    status: str


class AnswerSubmission(BaseModel):
    answer_text: str = Field(min_length=1, max_length=5000)
