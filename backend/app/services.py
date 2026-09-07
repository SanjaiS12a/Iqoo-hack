from collections import defaultdict
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .academic_models import Portion, PortionTopic, Question, Submission
from .auth import hash_password
from .models import Classroom, TeacherAssignment, User


def classroom_json(classroom: Classroom, student_count: int = 0) -> dict:
    return {
        "id": classroom.id,
        "name": classroom.name,
        "subject": classroom.subject,
        "grade": classroom.grade,
        "section": classroom.section,
        "join_code": classroom.join_code,
        "student_count": student_count,
    }


def user_json(user: User) -> dict:
    classroom = user.classroom
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "class_id": user.class_id,
        "class_name": classroom.name if classroom else None,
        "grade": classroom.grade if classroom else None,
        "section": classroom.section if classroom else None,
        "avatar_color": user.avatar_color,
    }


def seed_control_database(db: Session) -> dict[str, Classroom]:
    if db.scalar(select(func.count(User.id))) or 0:
        return {item.join_code: item for item in db.scalars(select(Classroom))}
    classes = [
        Classroom(name="Grade 9 · Section A", subject="Mathematics", grade=9, section="A", join_code="MATH9A"),
        Classroom(name="Grade 6 · Section B", subject="Science", grade=6, section="B", join_code="SCI6B"),
        Classroom(name="Grade 2 · Section A", subject="Integrated Studies", grade=2, section="A", join_code="LEARN2A"),
        Classroom(name="Grade 12 · Section A", subject="Physics", grade=12, section="A", join_code="PHY12A"),
    ]
    db.add_all(classes)
    db.flush()
    by_code = {item.join_code: item for item in classes}
    hashed = hash_password("demo1234")
    users = [
        User(name="School Administrator", email="admin@classmind.demo", password_hash=hashed, role="admin", avatar_color="#5b4bb7"),
        User(name="Meera Sharma", email="meera@classmind.demo", password_hash=hashed, role="teacher", avatar_color="#0f766e"),
        User(name="Rohan Verma", email="rohan@classmind.demo", password_hash=hashed, role="teacher", avatar_color="#2563a5"),
        User(name="Aarav Patel", email="aarav@classmind.demo", password_hash=hashed, role="student", class_id=by_code["MATH9A"].id, avatar_color="#d97706"),
    ]
    db.add_all(users)
    db.flush()
    meera, rohan = users[1], users[2]
    db.add_all([
        TeacherAssignment(teacher_id=meera.id, class_id=by_code["MATH9A"].id),
        TeacherAssignment(teacher_id=meera.id, class_id=by_code["SCI6B"].id),
        TeacherAssignment(teacher_id=rohan.id, class_id=by_code["LEARN2A"].id),
        TeacherAssignment(teacher_id=rohan.id, class_id=by_code["PHY12A"].id),
    ])
    for code, count in [("MATH9A", 27), ("SCI6B", 24), ("LEARN2A", 22), ("PHY12A", 20)]:
        classroom = by_code[code]
        for number in range(2, count + 1):
            db.add(User(
                name=f"Grade {classroom.grade} Learner {number:02d}",
                email=f"g{classroom.grade}{classroom.section.lower()}student{number:02d}@classmind.demo",
                password_hash=hashed,
                role="student",
                class_id=classroom.id,
                avatar_color="#64748b",
            ))
    db.commit()
    return by_code


def seed_grade_database(grade_db: Session, classroom: Classroom, student_ids: list[int]) -> None:
    existing = grade_db.scalar(select(func.count(Portion.id)).where(Portion.class_id == classroom.id)) or 0
    if existing:
        return
    subject = classroom.subject
    if classroom.grade == 9:
        title = "Term 1 · Linear Equations"
        topics = [
            ("Solving linear equations", "Solve one-variable equations using balancing operations"),
            ("Expanding brackets", "Apply the distributive property to every term"),
            ("Equations with fractions", "Use inverse operations to remove fractional coefficients"),
            ("Variables on both sides", "Collect variable terms and constants systematically"),
        ]
        questions = [
            ("linear-sign-demo", topics[0][0], "transposition", "Solve 2x + 4 = 10. Show every step.", "x = 3", .94),
            ("distribution-demo", topics[1][0], "distribution", "Solve 3(x + 2) = 18. Show how you expand the bracket.", "x = 4", .87),
            ("fractions-demo", topics[2][0], "fractions", "Solve x/3 + 2 = 6. Show how you remove the fraction.", "x = 12", .81),
            ("variables-both-sides", topics[3][0], "variables_both_sides", "Solve 5x - 3 = 2x + 9. Show each balancing operation.", "x = 4", .90),
        ]
    else:
        title = f"Grade {classroom.grade} · Current Portion"
        topics = [(f"{subject} foundations", f"Understand the current Grade {classroom.grade} {subject.lower()} concepts")]
        questions = [(f"g{classroom.grade}-{classroom.section}-foundation", topics[0][0], "foundations", f"Explain one important idea from the current {subject} portion.", "clear explanation", .75)]
    portion = Portion(class_id=classroom.id, title=title, subject=subject, original_filename="seeded-demo.pdf", stored_filename="seeded-demo.pdf", status="published", provider="demo", created_by=0, published_at=datetime.now(UTC).replace(tzinfo=None))
    grade_db.add(portion)
    grade_db.flush()
    grade_db.add_all([PortionTopic(portion_id=portion.id, title=name, learning_outcome=outcome, sequence=index + 1) for index, (name, outcome) in enumerate(topics)])
    question_rows = []
    for slug, topic, concept, text, answer, weight in questions:
        row = Question(class_id=classroom.id, portion_id=portion.id, slug=slug, subject=subject, topic=topic, concept_tag=concept, text=text, hint="Keep both sides balanced and show one operation per line.", correct_answer=answer, difficulty="Core", exam_frequency_score=weight)
        grade_db.add(row)
        question_rows.append(row)
    grade_db.flush()
    if classroom.grade == 9 and student_ids:
        patterns = [
            ("sign_error_transposition", "Sign error while moving terms across the equals sign", 14, question_rows[0]),
            ("incomplete_distribution", "Multiplier was not distributed to every term", 9, question_rows[1]),
            ("fraction_inverse_error", "Inverse operation with fractions was reversed", 6, question_rows[2]),
        ]
        for tag, label, count, question in patterns:
            for index, student_id in enumerate(student_ids[:count]):
                grade_db.add(Submission(class_id=classroom.id, student_id=student_id, question_id=question.id, answer_text="Synthetic classroom response", is_correct=False, misconception_tag=tag, misconception_label=label, micro_explanation="Synthetic demo activity", confidence=.93, created_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=index * 7 + 12)))
    grade_db.commit()


def question_json(question: Question) -> dict:
    return {
        "id": question.id,
        "portion_id": question.portion_id,
        "slug": question.slug,
        "subject": question.subject,
        "topic": question.topic,
        "concept_tag": question.concept_tag,
        "text": question.text,
        "hint": question.hint,
        "difficulty": question.difficulty,
        "exam_frequency_score": question.exam_frequency_score,
    }


def dashboard_data(academic_db: Session, classroom: Classroom, students: list[User]) -> dict:
    submissions = list(academic_db.scalars(select(Submission).where(Submission.class_id == classroom.id).order_by(Submission.created_at.desc())))
    names = {student.id: student.name for student in students}
    total = len(submissions)
    correct = sum(item.is_correct for item in submissions)
    grouped: dict[str, dict] = {}
    for item in submissions:
        if item.misconception_tag:
            entry = grouped.setdefault(item.misconception_tag, {"tag": item.misconception_tag, "label": item.misconception_label, "students": set(), "events": 0})
            entry["students"].add(item.student_id)
            entry["events"] += 1
    misconceptions = [{"tag": value["tag"], "label": value["label"], "affected_students": len(value["students"]), "events": value["events"], "class_percentage": round(len(value["students"]) / max(len(students), 1) * 100)} for value in grouped.values()]
    misconceptions.sort(key=lambda item: item["affected_students"], reverse=True)
    topic_data: dict[str, list[bool]] = defaultdict(list)
    for item in submissions:
        topic_data[item.question.topic].append(item.is_correct)
    topics = [{"topic": topic, "accuracy": round(sum(results) / len(results) * 100), "attempts": len(results)} for topic, results in topic_data.items()]
    recent = [{"id": item.id, "student_name": names.get(item.student_id, "Learner"), "topic": item.question.topic, "is_correct": item.is_correct, "misconception_label": item.misconception_label, "created_at": item.created_at.isoformat()} for item in submissions[:8]]
    return {
        "classroom": {**classroom_json(classroom, len(students))},
        "summary": {"active_students": len({item.student_id for item in submissions}), "total_students": len(students), "accuracy": round(correct / total * 100) if total else 0, "questions_answered": total},
        "misconceptions": misconceptions,
        "topics": topics,
        "recent_activity": recent,
        "demo_data": True,
    }
