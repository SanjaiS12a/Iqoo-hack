from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class SubmissionCreate(BaseModel):
    question_id: int
    answer_text: str = Field(min_length=1, max_length=4000)


class DoubtCreate(BaseModel):
    doubt_text: str = Field(min_length=3, max_length=2000)


class PlanItemUpdate(BaseModel):
    completed: bool


class ReteachCreate(BaseModel):
    misconception_tag: str = Field(min_length=2, max_length=100)
    misconception_label: str = Field(min_length=2, max_length=180)
    affected_students: int = Field(ge=1, le=1000)


class Diagnosis(BaseModel):
    is_correct: bool
    misconception_tag: str | None
    misconception_label: str | None
    micro_explanation: str
    confidence: float = Field(ge=0, le=1)


class TutorReply(BaseModel):
    concept_tag: str
    response: str
