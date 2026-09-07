from collections import defaultdict
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .auth import hash_password
from .models import Classroom, Doubt, Question, Submission, User


QUESTIONS = [
    {
        "slug": "linear-sign-demo",
        "subject": "Mathematics",
        "topic": "Solving linear equations",
        "concept_tag": "transposition",
        "text": "Solve 2x + 4 = 10. Show every step.",
        "hint": "Keep the equation balanced: undo +4 first.",
        "correct_answer": "x = 3",
        "difficulty": "Foundation",
        "exam_frequency_score": 0.94,
    },
    {
        "slug": "distribution-demo",
        "subject": "Mathematics",
        "topic": "Expanding brackets",
        "concept_tag": "distribution",
        "text": "Solve 3(x + 2) = 18. Show how you expand the bracket.",
        "hint": "The 3 multiplies every term inside the bracket.",
        "correct_answer": "x = 4",
        "difficulty": "Core",
        "exam_frequency_score": 0.87,
    },
    {
        "slug": "fractions-demo",
        "subject": "Mathematics",
        "topic": "Equations with fractions",
        "concept_tag": "fractions",
        "text": "Solve x/3 + 2 = 6. Show how you remove the fraction.",
        "hint": "First isolate x/3, then multiply both sides by 3.",
        "correct_answer": "x = 12",
        "difficulty": "Core",
        "exam_frequency_score": 0.81,
    },
    {
        "slug": "variables-both-sides",
        "subject": "Mathematics",
        "topic": "Variables on both sides",
        "concept_tag": "variables_both_sides",
        "text": "Solve 5x - 3 = 2x + 9. Show each balancing operation.",
        "hint": "Collect variable terms on one side first.",
        "correct_answer": "x = 4",
        "difficulty": "Challenge",
        "exam_frequency_score": 0.9,
    },
]


def seed_database(db: Session) -> None:
    if db.scalar(select(func.count(User.id))) or 0:
        return
    classroom = Classroom(name="9A · Equation Explorers", subject="Mathematics", grade="Class 9", join_code="MATH9A")
    db.add(classroom)
    db.flush()
    hashed = hash_password("demo1234")
    teacher = User(
        name="Meera Sharma",
        email="meera@classmind.demo",
        password_hash=hashed,
        role="teacher",
        class_id=classroom.id,
        avatar_color="#0f766e",
    )
    student = User(
        name="Aarav Patel",
        email="aarav@classmind.demo",
        password_hash=hashed,
        role="student",
        class_id=classroom.id,
        avatar_color="#d97706",
    )
    db.add_all([teacher, student])
    for i in range(2, 41):
        db.add(
            User(
                name=f"Demo Learner {i:02d}",
                email=f"student{i:02d}@classmind.demo",
                password_hash=hashed,
                role="student",
                class_id=classroom.id,
                avatar_color="#64748b",
            )
        )
    db.flush()
    question_rows = [Question(**question) for question in QUESTIONS]
    db.add_all(question_rows)
    db.flush()

    students = list(db.scalars(select(User).where(User.role == "student").order_by(User.id)))
    tags = [
        ("sign_error_transposition", "Sign error while moving terms across the equals sign", 14, question_rows[0]),
        ("incomplete_distribution", "Multiplier was not distributed to every term", 9, question_rows[1]),
        ("fraction_inverse_error", "Inverse operation with fractions was reversed", 6, question_rows[2]),
    ]
    for tag, label, count, question in tags:
        for index, learner in enumerate(students[:count]):
            db.add(
                Submission(
                    student_id=learner.id,
                    question_id=question.id,
                    answer_text="Seeded classroom response for demonstration",
                    is_correct=False,
                    misconception_tag=tag,
                    misconception_label=label,
                    micro_explanation="Synthetic demo activity",
                    confidence=0.93,
                    created_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=index * 7 + 12),
                )
            )
    for learner in students[14:31]:
        db.add(
            Submission(
                student_id=learner.id,
                question_id=question_rows[0].id,
                answer_text="x = 3",
                is_correct=True,
                misconception_tag=None,
                misconception_label=None,
                micro_explanation="Synthetic demo activity",
                confidence=0.99,
                created_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=4),
            )
        )
    db.commit()


def user_json(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "class_id": user.class_id,
        "class_name": user.classroom.name if user.classroom else None,
        "avatar_color": user.avatar_color,
    }


def question_json(question: Question) -> dict:
    return {
        "id": question.id,
        "slug": question.slug,
        "subject": question.subject,
        "topic": question.topic,
        "concept_tag": question.concept_tag,
        "text": question.text,
        "hint": question.hint,
        "difficulty": question.difficulty,
        "exam_frequency_score": question.exam_frequency_score,
    }


def dashboard_data(db: Session, class_id: int) -> dict:
    students = list(db.scalars(select(User).where(User.class_id == class_id, User.role == "student")))
    submissions = list(
        db.scalars(
            select(Submission)
            .join(User, Submission.student_id == User.id)
            .where(User.class_id == class_id)
            .order_by(Submission.created_at.desc())
        )
    )
    total = len(submissions)
    correct = sum(1 for item in submissions if item.is_correct)
    grouped: dict[str, dict] = {}
    for item in submissions:
        if not item.misconception_tag:
            continue
        entry = grouped.setdefault(
            item.misconception_tag,
            {"tag": item.misconception_tag, "label": item.misconception_label, "students": set(), "events": 0},
        )
        entry["students"].add(item.student_id)
        entry["events"] += 1
    misconceptions = [
        {
            "tag": entry["tag"],
            "label": entry["label"],
            "affected_students": len(entry["students"]),
            "events": entry["events"],
            "class_percentage": round(len(entry["students"]) / max(len(students), 1) * 100),
        }
        for entry in grouped.values()
    ]
    misconceptions.sort(key=lambda item: item["affected_students"], reverse=True)
    topic_data: dict[str, list[bool]] = defaultdict(list)
    for item in submissions:
        topic_data[item.question.topic].append(item.is_correct)
    topics = [
        {"topic": topic, "accuracy": round(sum(results) / len(results) * 100), "attempts": len(results)}
        for topic, results in topic_data.items()
    ]
    recent = [
        {
            "id": item.id,
            "student_name": item.student.name,
            "topic": item.question.topic,
            "is_correct": item.is_correct,
            "misconception_label": item.misconception_label,
            "created_at": item.created_at.isoformat(),
        }
        for item in submissions[:8]
    ]
    return {
        "classroom": {"id": class_id, "name": students[0].classroom.name if students else "Class", "student_count": len(students)},
        "summary": {
            "active_students": len({item.student_id for item in submissions}),
            "total_students": len(students),
            "accuracy": round(correct / total * 100) if total else 0,
            "questions_answered": total,
        },
        "misconceptions": misconceptions,
        "topics": topics,
        "recent_activity": recent,
        "demo_data": True,
    }
