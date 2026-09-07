from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .academic_models import Doubt, Portion, PortionTopic, Question, ReteachScript, StudyPlan, StudyPlanItem, Submission
from .ai import build_ai_provider
from .auth import create_token, current_user_dependency, require_role, verify_password
from .config import get_settings
from .content_ai import build_content_provider
from .database import Base, build_database, session_dependency
from .grade_database import GradeDatabaseRegistry
from .models import Classroom, TeacherAssignment, User
from .schemas import AdminClassCreate, DoubtCreate, LoginRequest, PlanItemUpdate, PortionEdit, ReteachCreate, SubmissionCreate
from .services import classroom_json, dashboard_data, question_json, seed_control_database, seed_grade_database, user_json
from .storage import LocalPortionStorage, validate_upload


def create_app(database_url: str | None = None, grade_database_dir: str | Path | None = None, upload_dir: str | Path | None = None) -> FastAPI:
    settings = get_settings()
    engine, session_factory = build_database(database_url or settings.database_url)
    grade_registry = GradeDatabaseRegistry(grade_database_dir or settings.grade_database_dir, settings.grade_database_url_template if grade_database_dir is None else None)
    storage = LocalPortionStorage(upload_dir or settings.upload_dir)
    content_ai = build_content_provider(settings)
    if settings.ai_provider == "gemini":
        answer_ai = build_ai_provider("gemini", settings.gemini_api_key, settings.gemini_model, "https://generativelanguage.googleapis.com/v1beta/openai/")
    elif settings.ai_provider == "local":
        answer_ai = build_ai_provider("local", "local-model", settings.local_ai_model, settings.local_ai_base_url)
    else:
        answer_ai = build_ai_provider(settings.ai_provider, settings.openai_api_key, settings.openai_model)

    def get_db():
        yield from session_dependency(session_factory)

    current_user = current_user_dependency(get_db, settings.jwt_secret)
    student_user = require_role("student", current_user)
    teacher_user = require_role("teacher", current_user)
    admin_user = require_role("admin", current_user)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        Base.metadata.create_all(engine)
        for grade in range(1, 13):
            grade_registry.initialize(grade)
        with session_factory() as db:
            seed_control_database(db)
            classrooms = list(db.scalars(select(Classroom)))
            for classroom in classrooms:
                students = list(db.scalars(select(User).where(User.class_id == classroom.id, User.role == "student")))
                with grade_registry.session(classroom.grade) as grade_db:
                    seed_grade_database(grade_db, classroom, [student.id for student in students])
        yield
        grade_registry.dispose()

    app = FastAPI(title=settings.app_name, version="2.0.0", lifespan=lifespan)
    app.state.grade_registry = grade_registry
    app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(",")], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

    def student_class(user: User, db: Session) -> Classroom:
        if not user.class_id:
            raise HTTPException(status_code=409, detail="Student has not been assigned to a class")
        classroom = db.get(Classroom, user.class_id)
        if classroom is None:
            raise HTTPException(status_code=404, detail="Assigned class was not found")
        return classroom

    def assigned_class(user: User, class_id: int, db: Session) -> Classroom:
        classroom = db.get(Classroom, class_id)
        if classroom is None:
            raise HTTPException(status_code=404, detail="Class not found")
        assignment = db.scalar(select(TeacherAssignment).where(TeacherAssignment.teacher_id == user.id, TeacherAssignment.class_id == class_id))
        if assignment is None:
            raise HTTPException(status_code=403, detail="This class is not assigned to you")
        return classroom

    def class_students(class_id: int, db: Session) -> list[User]:
        return list(db.scalars(select(User).where(User.class_id == class_id, User.role == "student").order_by(User.name)))

    def portion_json(portion: Portion) -> dict:
        return {
            "id": portion.id,
            "class_id": portion.class_id,
            "title": portion.title,
            "subject": portion.subject,
            "original_filename": portion.original_filename,
            "status": portion.status,
            "provider": portion.provider,
            "created_at": portion.created_at.isoformat(),
            "published_at": portion.published_at.isoformat() if portion.published_at else None,
            "topics": [{"id": x.id, "title": x.title, "learning_outcome": x.learning_outcome, "sequence": x.sequence} for x in portion.topics],
            "questions": [{"id": x.id, "text": x.text, "expected_answer": x.correct_answer, "difficulty": x.difficulty, "topic": x.topic, "exam_weight": x.exam_frequency_score} for x in portion.questions],
        }

    @app.get("/api/health")
    def health():
        return {"status": "ok", "ai_provider": settings.ai_provider, "model": settings.openai_model, "grade_databases": 12}

    @app.post("/api/auth/login")
    def login(payload: LoginRequest, db: Session = Depends(get_db)):
        user = db.scalar(select(User).where(func.lower(User.email) == payload.email.lower()))
        if user is None or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        return {"access_token": create_token(user, settings.jwt_secret, settings.jwt_expire_minutes), "token_type": "bearer", "user": user_json(user)}

    @app.get("/api/auth/me")
    def me(user: User = Depends(current_user)):
        return user_json(user)

    @app.get("/api/admin/grades")
    def admin_grades(_: User = Depends(admin_user), db: Session = Depends(get_db)):
        classrooms = list(db.scalars(select(Classroom).order_by(Classroom.grade, Classroom.section)))
        result = []
        for grade in range(1, 13):
            items = [item for item in classrooms if item.grade == grade]
            result.append({"grade": grade, "classes": [classroom_json(item, db.scalar(select(func.count(User.id)).where(User.class_id == item.id, User.role == "student")) or 0) for item in items]})
        return result

    @app.get("/api/admin/classes")
    def admin_classes(_: User = Depends(admin_user), db: Session = Depends(get_db)):
        return [classroom_json(item, db.scalar(select(func.count(User.id)).where(User.class_id == item.id, User.role == "student")) or 0) for item in db.scalars(select(Classroom).order_by(Classroom.grade, Classroom.section))]

    @app.get("/api/admin/users")
    def admin_users(_: User = Depends(admin_user), db: Session = Depends(get_db)):
        return [user_json(user) for user in db.scalars(select(User).order_by(User.role, User.name))]

    @app.post("/api/admin/classes", status_code=201)
    def create_class(payload: AdminClassCreate, _: User = Depends(admin_user), db: Session = Depends(get_db)):
        class_data = payload.model_dump()
        class_data["section"] = payload.section.strip().upper()
        class_data["join_code"] = payload.join_code or f"G{payload.grade:02d}{''.join(character for character in class_data['section'] if character.isalnum())}"[:20]
        classroom = Classroom(**class_data)
        db.add(classroom)
        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail="Grade, section, or join code already exists") from exc
        db.refresh(classroom)
        grade_registry.initialize(classroom.grade)
        return classroom_json(classroom)

    @app.post("/api/admin/classes/{class_id}/teachers/{teacher_id}")
    def assign_teacher(class_id: int, teacher_id: int, _: User = Depends(admin_user), db: Session = Depends(get_db)):
        classroom, teacher = db.get(Classroom, class_id), db.get(User, teacher_id)
        if not classroom or not teacher or teacher.role != "teacher":
            raise HTTPException(status_code=404, detail="Teacher or class not found")
        existing = db.scalar(select(TeacherAssignment).where(TeacherAssignment.class_id == class_id, TeacherAssignment.teacher_id == teacher_id))
        if not existing:
            db.add(TeacherAssignment(class_id=class_id, teacher_id=teacher_id)); db.commit()
        return {"teacher_id": teacher_id, "class_id": class_id}

    @app.post("/api/admin/classes/{class_id}/students/{student_id}")
    def place_student(class_id: int, student_id: int, _: User = Depends(admin_user), db: Session = Depends(get_db)):
        classroom, student = db.get(Classroom, class_id), db.get(User, student_id)
        if not classroom or not student or student.role != "student":
            raise HTTPException(status_code=404, detail="Student or class not found")
        student.class_id = classroom.id
        db.commit(); db.refresh(student)
        return user_json(student)

    @app.get("/api/teacher/classes")
    def teacher_classes(user: User = Depends(teacher_user), db: Session = Depends(get_db)):
        classrooms = list(db.scalars(select(Classroom).join(TeacherAssignment).where(TeacherAssignment.teacher_id == user.id).order_by(Classroom.grade, Classroom.section)))
        return [classroom_json(item, db.scalar(select(func.count(User.id)).where(User.class_id == item.id, User.role == "student")) or 0) for item in classrooms]

    @app.get("/api/teacher/classes/{class_id}/dashboard")
    def teacher_dashboard_for_class(class_id: int, user: User = Depends(teacher_user), db: Session = Depends(get_db)):
        classroom = assigned_class(user, class_id, db)
        students = class_students(class_id, db)
        with grade_registry.session(classroom.grade) as grade_db:
            return dashboard_data(grade_db, classroom, students)

    @app.get("/api/teacher/dashboard")
    def teacher_dashboard(user: User = Depends(teacher_user), db: Session = Depends(get_db)):
        assignment = db.scalar(select(TeacherAssignment).where(TeacherAssignment.teacher_id == user.id).order_by(TeacherAssignment.id))
        if not assignment:
            raise HTTPException(status_code=404, detail="Teacher has no assigned classes")
        classroom = db.get(Classroom, assignment.class_id)
        with grade_registry.session(classroom.grade) as grade_db:
            return dashboard_data(grade_db, classroom, class_students(classroom.id, db))

    @app.get("/api/teacher/classes/{class_id}/students")
    def teacher_students_for_class(class_id: int, user: User = Depends(teacher_user), db: Session = Depends(get_db)):
        classroom = assigned_class(user, class_id, db)
        students = class_students(class_id, db)
        with grade_registry.session(classroom.grade) as grade_db:
            result = []
            for student in students:
                attempts = list(grade_db.scalars(select(Submission).where(Submission.class_id == class_id, Submission.student_id == student.id)))
                result.append({"id": student.id, "name": student.name, "attempts": len(attempts), "accuracy": round(sum(x.is_correct for x in attempts) / len(attempts) * 100) if attempts else 0, "active_gaps": len({x.misconception_tag for x in attempts if x.misconception_tag})})
            return result

    @app.get("/api/teacher/students")
    def teacher_students(user: User = Depends(teacher_user), db: Session = Depends(get_db)):
        assignment = db.scalar(select(TeacherAssignment).where(TeacherAssignment.teacher_id == user.id).order_by(TeacherAssignment.id))
        if not assignment:
            return []
        return teacher_students_for_class(assignment.class_id, user, db)

    @app.get("/api/teacher/classes/{class_id}/portions")
    def portions(class_id: int, user: User = Depends(teacher_user), db: Session = Depends(get_db)):
        classroom = assigned_class(user, class_id, db)
        with grade_registry.session(classroom.grade) as grade_db:
            return [portion_json(item) for item in grade_db.scalars(select(Portion).where(Portion.class_id == class_id).order_by(Portion.created_at.desc()))]

    @app.post("/api/teacher/classes/{class_id}/portions", status_code=201)
    async def upload_portion(class_id: int, file: UploadFile = File(...), user: User = Depends(teacher_user), db: Session = Depends(get_db)):
        classroom = assigned_class(user, class_id, db)
        content = await file.read()
        media_type = file.content_type or "application/octet-stream"
        try:
            validate_upload(media_type, content)
        except ValueError as exc:
            raise HTTPException(status_code=415, detail=str(exc)) from exc
        stored = storage.save(classroom.grade, class_id, file.filename or "portion", content)
        try:
            extracted = content_ai.extract(file.filename or "portion", media_type, content)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Portion extraction failed: {exc}") from exc
        with grade_registry.session(classroom.grade) as grade_db:
            portion = Portion(class_id=class_id, title=extracted.title, subject=extracted.subject, original_filename=file.filename or "portion", stored_filename=stored, status="draft", provider=content_ai.name, created_by=user.id)
            grade_db.add(portion); grade_db.flush()
            for topic in extracted.topics:
                grade_db.add(PortionTopic(portion_id=portion.id, **topic.model_dump()))
            for index, question in enumerate(extracted.questions):
                grade_db.add(Question(class_id=class_id, portion_id=portion.id, slug=f"portion-{portion.id}-{index}-{uuid4().hex[:6]}", subject=extracted.subject, topic=question.topic, concept_tag=question.topic.lower().replace(" ", "_"), text=question.text, hint="Review this topic in the uploaded portion and show each step.", correct_answer=question.expected_answer, difficulty=question.difficulty, exam_frequency_score=question.exam_weight))
            grade_db.commit(); grade_db.refresh(portion)
            return portion_json(portion)

    @app.put("/api/teacher/classes/{class_id}/portions/{portion_id}")
    def update_portion(class_id: int, portion_id: int, payload: PortionEdit, user: User = Depends(teacher_user), db: Session = Depends(get_db)):
        classroom = assigned_class(user, class_id, db)
        with grade_registry.session(classroom.grade) as grade_db:
            portion = grade_db.scalar(select(Portion).where(Portion.id == portion_id, Portion.class_id == class_id))
            if not portion or portion.status != "draft":
                raise HTTPException(status_code=409, detail="Only a draft portion can be edited")
            portion.title, portion.subject = payload.title, payload.subject
            portion.topics.clear(); portion.questions.clear(); grade_db.flush()
            for topic in payload.topics:
                grade_db.add(PortionTopic(portion_id=portion.id, **topic.model_dump()))
            for index, question in enumerate(payload.questions):
                grade_db.add(Question(class_id=class_id, portion_id=portion.id, slug=f"portion-{portion.id}-edit-{index}-{uuid4().hex[:6]}", subject=payload.subject, topic=question.topic, concept_tag=question.topic.lower().replace(" ", "_"), text=question.text, hint="Review the published portion, then show each reasoning step.", correct_answer=question.expected_answer, difficulty=question.difficulty, exam_frequency_score=question.exam_weight))
            grade_db.commit(); grade_db.refresh(portion)
            return portion_json(portion)

    @app.post("/api/teacher/classes/{class_id}/portions/{portion_id}/publish")
    def publish_portion(class_id: int, portion_id: int, user: User = Depends(teacher_user), db: Session = Depends(get_db)):
        classroom = assigned_class(user, class_id, db)
        with grade_registry.session(classroom.grade) as grade_db:
            portion = grade_db.scalar(select(Portion).where(Portion.id == portion_id, Portion.class_id == class_id))
            if not portion:
                raise HTTPException(status_code=404, detail="Portion not found")
            if not portion.topics or not portion.questions:
                raise HTTPException(status_code=409, detail="Add at least one topic and question before publishing")
            if portion.status != "published":
                for old in grade_db.scalars(select(Portion).where(Portion.class_id == class_id, Portion.status == "published")):
                    old.status = "archived"
                portion.status = "published"; portion.published_at = datetime.now(UTC).replace(tzinfo=None); grade_db.commit()
            return portion_json(portion)

    @app.get("/api/student/questions")
    def questions(user: User = Depends(student_user), db: Session = Depends(get_db)):
        classroom = student_class(user, db)
        with grade_registry.session(classroom.grade) as grade_db:
            published_ids = select(Portion.id).where(Portion.class_id == classroom.id, Portion.status == "published")
            rows = grade_db.scalars(select(Question).where(Question.class_id == classroom.id, Question.portion_id.in_(published_ids)).order_by(Question.id))
            return [question_json(item) for item in rows]

    @app.get("/api/student/overview")
    def student_overview(user: User = Depends(student_user), db: Session = Depends(get_db)):
        classroom = student_class(user, db)
        with grade_registry.session(classroom.grade) as grade_db:
            submissions = list(grade_db.scalars(select(Submission).where(Submission.class_id == classroom.id, Submission.student_id == user.id).order_by(Submission.created_at.desc())))
            correct = sum(item.is_correct for item in submissions)
            active = grade_db.scalar(select(Portion).where(Portion.class_id == classroom.id, Portion.status == "published").order_by(Portion.published_at.desc()))
            return {"accuracy": round(correct / len(submissions) * 100) if submissions else 0, "questions_attempted": len(submissions), "streak": min(len(submissions), 5), "active_gaps": len({x.misconception_tag for x in submissions if x.misconception_tag}), "active_portion": portion_json(active) if active else None, "recent": [{"id": item.id, "topic": item.question.topic, "is_correct": item.is_correct, "misconception_label": item.misconception_label, "created_at": item.created_at.isoformat()} for item in submissions[:5]]}

    @app.post("/api/student/submissions", status_code=201)
    def submit(payload: SubmissionCreate, user: User = Depends(student_user), db: Session = Depends(get_db)):
        classroom = student_class(user, db)
        with grade_registry.session(classroom.grade) as grade_db:
            question = grade_db.scalar(select(Question).join(Portion).where(Question.id == payload.question_id, Question.class_id == classroom.id, Portion.status == "published"))
            if not question:
                raise HTTPException(status_code=404, detail="Published question not found")
            diagnosis = answer_ai.diagnose(question, payload.answer_text)
            row = Submission(class_id=classroom.id, student_id=user.id, question_id=question.id, answer_text=payload.answer_text, **diagnosis.model_dump())
            grade_db.add(row); grade_db.commit(); grade_db.refresh(row)
            return {"id": row.id, **diagnosis.model_dump(), "created_at": row.created_at.isoformat()}

    @app.get("/api/student/doubts")
    def doubts(user: User = Depends(student_user), db: Session = Depends(get_db)):
        classroom = student_class(user, db)
        with grade_registry.session(classroom.grade) as grade_db:
            rows = grade_db.scalars(select(Doubt).where(Doubt.class_id == classroom.id, Doubt.student_id == user.id).order_by(Doubt.created_at.desc()).limit(20))
            return [{"id": row.id, "doubt_text": row.doubt_text, "concept_tag": row.concept_tag, "ai_response": row.ai_response, "created_at": row.created_at.isoformat()} for row in rows]

    @app.post("/api/student/doubts", status_code=201)
    def ask_doubt(payload: DoubtCreate, user: User = Depends(student_user), db: Session = Depends(get_db)):
        classroom = student_class(user, db); reply = answer_ai.tutor(payload.doubt_text)
        with grade_registry.session(classroom.grade) as grade_db:
            row = Doubt(class_id=classroom.id, student_id=user.id, doubt_text=payload.doubt_text, concept_tag=reply.concept_tag, ai_response=reply.response)
            grade_db.add(row); grade_db.commit(); grade_db.refresh(row)
            return {"id": row.id, "doubt_text": row.doubt_text, "concept_tag": row.concept_tag, "ai_response": row.ai_response, "created_at": row.created_at.isoformat()}

    def plan_json(plan: StudyPlan | None) -> dict:
        if not plan:
            return {"id": None, "generated_at": None, "items": []}
        return {"id": plan.id, "generated_at": plan.generated_at.isoformat(), "items": [{"id": x.id, "topic": x.topic, "reason": x.reason, "priority_score": x.priority_score, "estimated_minutes": x.estimated_minutes, "completed": x.completed} for x in sorted(plan.items, key=lambda x: x.priority_score, reverse=True)]}

    @app.get("/api/student/study-plan")
    def get_plan(user: User = Depends(student_user), db: Session = Depends(get_db)):
        classroom = student_class(user, db)
        with grade_registry.session(classroom.grade) as grade_db:
            return plan_json(grade_db.scalar(select(StudyPlan).where(StudyPlan.class_id == classroom.id, StudyPlan.student_id == user.id).order_by(StudyPlan.generated_at.desc())))

    @app.post("/api/student/study-plan/generate", status_code=201)
    def generate_plan(user: User = Depends(student_user), db: Session = Depends(get_db)):
        classroom = student_class(user, db)
        with grade_registry.session(classroom.grade) as grade_db:
            portion = grade_db.scalar(select(Portion).where(Portion.class_id == classroom.id, Portion.status == "published").order_by(Portion.published_at.desc()))
            if not portion:
                raise HTTPException(status_code=409, detail="Your teacher has not published a portion yet")
            weaknesses: dict[str, int] = {}
            for row in grade_db.scalars(select(Submission).where(Submission.class_id == classroom.id, Submission.student_id == user.id, Submission.is_correct.is_(False))):
                weaknesses[row.question.topic] = weaknesses.get(row.question.topic, 0) + 1
            weights = {question.topic: max(question.exam_frequency_score * 100, 1) for question in portion.questions}
            plan = StudyPlan(class_id=classroom.id, student_id=user.id); grade_db.add(plan); grade_db.flush()
            for topic in portion.topics:
                score = weights.get(topic.title, 60) + min(weaknesses.get(topic.title, 0) * 12, 30)
                reason = f"Part of {portion.title}. " + (f"You have {weaknesses[topic.title]} learning signal(s) here." if weaknesses.get(topic.title) else "Scheduled from your teacher's published portion.")
                grade_db.add(StudyPlanItem(plan_id=plan.id, topic=topic.title, reason=reason, priority_score=score, estimated_minutes=15 + weaknesses.get(topic.title, 0) * 5))
            grade_db.commit(); grade_db.refresh(plan); return plan_json(plan)

    @app.patch("/api/student/study-plan/items/{item_id}")
    def update_plan_item(item_id: int, payload: PlanItemUpdate, user: User = Depends(student_user), db: Session = Depends(get_db)):
        classroom = student_class(user, db)
        with grade_registry.session(classroom.grade) as grade_db:
            item = grade_db.scalar(select(StudyPlanItem).join(StudyPlan).where(StudyPlanItem.id == item_id, StudyPlan.student_id == user.id, StudyPlan.class_id == classroom.id))
            if not item:
                raise HTTPException(status_code=404, detail="Plan item not found")
            item.completed = payload.completed; grade_db.commit(); return {"id": item.id, "completed": item.completed}

    @app.post("/api/teacher/classes/{class_id}/reteach", status_code=201)
    def reteach_for_class(class_id: int, payload: ReteachCreate, user: User = Depends(teacher_user), db: Session = Depends(get_db)):
        classroom = assigned_class(user, class_id, db); script = answer_ai.reteach(payload.misconception_label, payload.affected_students)
        with grade_registry.session(classroom.grade) as grade_db:
            row = ReteachScript(class_id=class_id, teacher_id=user.id, misconception_tag=payload.misconception_tag, script=script); grade_db.add(row); grade_db.commit(); grade_db.refresh(row)
            return {"id": row.id, "misconception_tag": row.misconception_tag, "script": row.script, "created_at": row.created_at.isoformat()}

    @app.post("/api/teacher/reteach", status_code=201)
    def reteach(payload: ReteachCreate, user: User = Depends(teacher_user), db: Session = Depends(get_db)):
        assignment = db.scalar(select(TeacherAssignment).where(TeacherAssignment.teacher_id == user.id).order_by(TeacherAssignment.id))
        if not assignment:
            raise HTTPException(status_code=404, detail="Teacher has no assigned classes")
        return reteach_for_class(assignment.class_id, payload, user, db)

    return app


app = create_app()
