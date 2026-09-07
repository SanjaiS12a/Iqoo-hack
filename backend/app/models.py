from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Classroom(Base):
    __tablename__ = "classrooms"
    __table_args__ = (UniqueConstraint("grade", "section", name="uq_grade_section"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    subject: Mapped[str] = mapped_column(String(80), default="General")
    grade: Mapped[int] = mapped_column(Integer, index=True)
    section: Mapped[str] = mapped_column(String(20))
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


class TeacherAssignment(Base):
    __tablename__ = "teacher_assignments"
    __table_args__ = (UniqueConstraint("teacher_id", "class_id", name="uq_teacher_class"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id"), index=True)
    teacher: Mapped[User] = relationship(foreign_keys=[teacher_id])
    classroom: Mapped[Classroom] = relationship(foreign_keys=[class_id])
