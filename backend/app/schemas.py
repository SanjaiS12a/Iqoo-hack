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


class AdminClassCreate(BaseModel):
    grade: int = Field(ge=1, le=12)
    section: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=2, max_length=120)
    subject: str = Field(min_length=2, max_length=80)
    join_code: str | None = Field(default=None, min_length=4, max_length=20)


class PortionTopicEdit(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    learning_outcome: str = Field(min_length=2, max_length=1000)
    sequence: int = Field(ge=1, le=100)


class PortionQuestionEdit(BaseModel):
    text: str = Field(min_length=3, max_length=2000)
    expected_answer: str = Field(min_length=1, max_length=1000)
    difficulty: str = Field(min_length=2, max_length=30)
    topic: str = Field(min_length=2, max_length=160)
    exam_weight: float = Field(ge=0, le=1)


class PortionEdit(BaseModel):
    title: str = Field(min_length=2, max_length=180)
    subject: str = Field(min_length=2, max_length=100)
    topics: list[PortionTopicEdit] = Field(min_length=1, max_length=30)
    questions: list[PortionQuestionEdit] = Field(min_length=1, max_length=100)
