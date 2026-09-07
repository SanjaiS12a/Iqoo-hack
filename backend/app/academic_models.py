from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class AcademicBase(DeclarativeBase):
    pass


class Portion(AcademicBase):
    __tablename__ = "portions"
    id: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(180))
    subject: Mapped[str] = mapped_column(String(100))
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), default="processing", index=True)
    provider: Mapped[str] = mapped_column(String(30), default="demo")
    created_by: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    topics: Mapped[list["PortionTopic"]] = relationship(cascade="all, delete-orphan", order_by="PortionTopic.sequence")
    questions: Mapped[list["Question"]] = relationship(cascade="all, delete-orphan", order_by="Question.id")


class PortionTopic(AcademicBase):
    __tablename__ = "portion_topics"
    id: Mapped[int] = mapped_column(primary_key=True)
    portion_id: Mapped[int] = mapped_column(ForeignKey("portions.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    learning_outcome: Mapped[str] = mapped_column(Text)
    sequence: Mapped[int] = mapped_column(Integer)


class Question(AcademicBase):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(Integer, index=True)
    portion_id: Mapped[int] = mapped_column(ForeignKey("portions.id"), index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    subject: Mapped[str] = mapped_column(String(100))
    topic: Mapped[str] = mapped_column(String(160), index=True)
    concept_tag: Mapped[str] = mapped_column(String(100))
    text: Mapped[str] = mapped_column(Text)
    hint: Mapped[str] = mapped_column(Text, default="Review the active portion and show each step.")
    correct_answer: Mapped[str] = mapped_column(String(200))
    difficulty: Mapped[str] = mapped_column(String(30))
    exam_frequency_score: Mapped[float] = mapped_column(Float)


class Submission(AcademicBase):
    __tablename__ = "submissions"
    id: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(Integer, index=True)
    student_id: Mapped[int] = mapped_column(Integer, index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    answer_text: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    misconception_tag: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    misconception_label: Mapped[str | None] = mapped_column(String(180), nullable=True)
    micro_explanation: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    question: Mapped[Question] = relationship()


class Doubt(AcademicBase):
    __tablename__ = "doubts"
    id: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(Integer, index=True)
    student_id: Mapped[int] = mapped_column(Integer, index=True)
    doubt_text: Mapped[str] = mapped_column(Text)
    concept_tag: Mapped[str] = mapped_column(String(100), index=True)
    ai_response: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class StudyPlan(AcademicBase):
    __tablename__ = "study_plans"
    id: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(Integer, index=True)
    student_id: Mapped[int] = mapped_column(Integer, index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    items: Mapped[list["StudyPlanItem"]] = relationship(cascade="all, delete-orphan", order_by="StudyPlanItem.priority_score.desc()")


class StudyPlanItem(AcademicBase):
    __tablename__ = "study_plan_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("study_plans.id"), index=True)
    topic: Mapped[str] = mapped_column(String(160))
    reason: Mapped[str] = mapped_column(Text)
    priority_score: Mapped[float] = mapped_column(Float)
    estimated_minutes: Mapped[int] = mapped_column(Integer)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)


class ReteachScript(AcademicBase):
    __tablename__ = "reteach_scripts"
    id: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(Integer, index=True)
    teacher_id: Mapped[int] = mapped_column(Integer)
    misconception_tag: Mapped[str] = mapped_column(String(100))
    script: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

