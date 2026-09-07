from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Classroom(Base):
    __tablename__ = "classrooms"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    subject: Mapped[str] = mapped_column(String(80), default="Mathematics")
    grade: Mapped[str] = mapped_column(String(40), default="Class 9")
    join_code: Mapped[str] = mapped_column(String(20), unique=True)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), index=True)
    class_id: Mapped[int | None] = mapped_column(ForeignKey("classrooms.id"), nullable=True)
    avatar_color: Mapped[str] = mapped_column(String(20), default="#0f766e")
    classroom: Mapped[Classroom | None] = relationship()


class Question(Base):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    subject: Mapped[str] = mapped_column(String(80))
    topic: Mapped[str] = mapped_column(String(120), index=True)
    concept_tag: Mapped[str] = mapped_column(String(80))
    text: Mapped[str] = mapped_column(Text)
    hint: Mapped[str] = mapped_column(Text)
    correct_answer: Mapped[str] = mapped_column(String(120))
    difficulty: Mapped[str] = mapped_column(String(20))
    exam_frequency_score: Mapped[float] = mapped_column(Float)


class Submission(Base):
    __tablename__ = "submissions"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    answer_text: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    misconception_tag: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    misconception_label: Mapped[str | None] = mapped_column(String(180), nullable=True)
    micro_explanation: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    student: Mapped[User] = relationship()
    question: Mapped[Question] = relationship()


class Doubt(Base):
    __tablename__ = "doubts"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    doubt_text: Mapped[str] = mapped_column(Text)
    concept_tag: Mapped[str] = mapped_column(String(100), index=True)
    ai_response: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class StudyPlan(Base):
    __tablename__ = "study_plans"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    items: Mapped[list["StudyPlanItem"]] = relationship(cascade="all, delete-orphan", order_by="StudyPlanItem.priority_score.desc()")


class StudyPlanItem(Base):
    __tablename__ = "study_plan_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("study_plans.id"), index=True)
    topic: Mapped[str] = mapped_column(String(120))
    reason: Mapped[str] = mapped_column(Text)
    priority_score: Mapped[float] = mapped_column(Float)
    estimated_minutes: Mapped[int] = mapped_column(Integer)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)


class ReteachScript(Base):
    __tablename__ = "reteach_scripts"
    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    class_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id"))
    misconception_tag: Mapped[str] = mapped_column(String(100))
    script: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
