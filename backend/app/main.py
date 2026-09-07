from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .ai import build_ai_provider
from .auth import create_token, current_user_dependency, require_role, verify_password
from .config import get_settings
from .database import Base, build_database, session_dependency
from .models import Doubt, Question, ReteachScript, StudyPlan, StudyPlanItem, Submission, User
from .schemas import DoubtCreate, LoginRequest, PlanItemUpdate, ReteachCreate, SubmissionCreate
from .services import dashboard_data, question_json, seed_database, user_json


def create_app(database_url: str | None = None) -> FastAPI:
    settings = get_settings()
    engine, session_factory = build_database(database_url or settings.database_url)

    def get_db():
        yield from session_dependency(session_factory)

    current_user = current_user_dependency(get_db, settings.jwt_secret)
    student_user = require_role("student", current_user)
    teacher_user = require_role("teacher", current_user)
    ai = build_ai_provider(settings.ai_provider, settings.openai_api_key, settings.openai_model)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        Base.metadata.create_all(engine)
        with session_factory() as db:
            seed_database(db)
        yield

    app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health():
        return {"status": "ok", "ai_provider": settings.ai_provider, "model": settings.openai_model}

    @app.post("/api/auth/login")
    def login(payload: LoginRequest, db: Session = Depends(get_db)):
        user = db.scalar(select(User).where(func.lower(User.email) == payload.email.lower()))
        if user is None or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        return {
            "access_token": create_token(user, settings.jwt_secret, settings.jwt_expire_minutes),
            "token_type": "bearer",
            "user": user_json(user),
        }

    @app.get("/api/auth/me")
    def me(user: User = Depends(current_user)):
        return user_json(user)

    @app.get("/api/student/questions")
    def questions(_: User = Depends(student_user), db: Session = Depends(get_db)):
        return [question_json(q) for q in db.scalars(select(Question).order_by(Question.id))]

    @app.get("/api/student/overview")
    def student_overview(user: User = Depends(student_user), db: Session = Depends(get_db)):
        submissions = list(db.scalars(select(Submission).where(Submission.student_id == user.id).order_by(Submission.created_at.desc())))
        correct = sum(1 for item in submissions if item.is_correct)
        recent = [
            {
                "id": item.id,
                "topic": item.question.topic,
                "is_correct": item.is_correct,
                "misconception_label": item.misconception_label,
                "created_at": item.created_at.isoformat(),
            }
            for item in submissions[:5]
        ]
        return {
            "accuracy": round(correct / len(submissions) * 100) if submissions else 0,
            "questions_attempted": len(submissions),
            "streak": min(len(submissions), 5),
            "active_gaps": len({s.misconception_tag for s in submissions if s.misconception_tag}),
            "recent": recent,
        }

    @app.post("/api/student/submissions", status_code=status.HTTP_201_CREATED)
    def submit(payload: SubmissionCreate, user: User = Depends(student_user), db: Session = Depends(get_db)):
        question = db.get(Question, payload.question_id)
        if question is None:
            raise HTTPException(status_code=404, detail="Question not found")
        diagnosis = ai.diagnose(question, payload.answer_text)
        row = Submission(
            student_id=user.id,
            question_id=question.id,
            answer_text=payload.answer_text,
            **diagnosis.model_dump(),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return {"id": row.id, **diagnosis.model_dump(), "created_at": row.created_at.isoformat()}

    @app.get("/api/student/doubts")
    def doubts(user: User = Depends(student_user), db: Session = Depends(get_db)):
        rows = db.scalars(select(Doubt).where(Doubt.student_id == user.id).order_by(Doubt.created_at.desc()).limit(20))
        return [
            {"id": row.id, "doubt_text": row.doubt_text, "concept_tag": row.concept_tag, "ai_response": row.ai_response, "created_at": row.created_at.isoformat()}
            for row in rows
        ]

    @app.post("/api/student/doubts", status_code=status.HTTP_201_CREATED)
    def ask_doubt(payload: DoubtCreate, user: User = Depends(student_user), db: Session = Depends(get_db)):
        reply = ai.tutor(payload.doubt_text)
        row = Doubt(student_id=user.id, doubt_text=payload.doubt_text, concept_tag=reply.concept_tag, ai_response=reply.response)
        db.add(row)
        db.commit()
        db.refresh(row)
        return {"id": row.id, "doubt_text": row.doubt_text, "concept_tag": row.concept_tag, "ai_response": row.ai_response, "created_at": row.created_at.isoformat()}

    def plan_json(plan: StudyPlan) -> dict:
        return {
            "id": plan.id,
            "generated_at": plan.generated_at.isoformat(),
            "items": [
                {"id": item.id, "topic": item.topic, "reason": item.reason, "priority_score": item.priority_score, "estimated_minutes": item.estimated_minutes, "completed": item.completed}
                for item in sorted(plan.items, key=lambda value: value.priority_score, reverse=True)
            ],
        }

    @app.get("/api/student/study-plan")
    def get_plan(user: User = Depends(student_user), db: Session = Depends(get_db)):
        plan = db.scalar(select(StudyPlan).where(StudyPlan.student_id == user.id).order_by(StudyPlan.generated_at.desc()))
        return plan_json(plan) if plan else {"id": None, "generated_at": None, "items": []}

    @app.post("/api/student/study-plan/generate", status_code=status.HTTP_201_CREATED)
    def generate_plan(user: User = Depends(student_user), db: Session = Depends(get_db)):
        weaknesses: dict[str, int] = {}
        for submission in db.scalars(select(Submission).where(Submission.student_id == user.id, Submission.is_correct.is_(False))):
            weaknesses[submission.question.topic] = weaknesses.get(submission.question.topic, 0) + 1
        topic_weights = {
            "Solving linear equations": 94,
            "Variables on both sides": 90,
            "Expanding brackets": 87,
            "Equations with fractions": 81,
        }
        plan = StudyPlan(student_id=user.id)
        db.add(plan)
        db.flush()
        for topic, weight in topic_weights.items():
            gap_count = weaknesses.get(topic, 0)
            score = float(weight + min(gap_count * 12, 30))
            reason = (
                f"You have {gap_count} recent misconception event{'s' if gap_count != 1 else ''} here, and this demo exam weight is {weight}%."
                if gap_count
                else f"High-value preventive practice with an illustrative demo exam weight of {weight}%."
            )
            db.add(StudyPlanItem(plan_id=plan.id, topic=topic, reason=reason, priority_score=score, estimated_minutes=15 + gap_count * 5))
        db.commit()
        db.refresh(plan)
        return plan_json(plan)

    @app.patch("/api/student/study-plan/items/{item_id}")
    def update_plan_item(item_id: int, payload: PlanItemUpdate, user: User = Depends(student_user), db: Session = Depends(get_db)):
        item = db.scalar(select(StudyPlanItem).join(StudyPlan).where(StudyPlanItem.id == item_id, StudyPlan.student_id == user.id))
        if item is None:
            raise HTTPException(status_code=404, detail="Plan item not found")
        item.completed = payload.completed
        db.commit()
        return {"id": item.id, "completed": item.completed}

    @app.get("/api/teacher/dashboard")
    def teacher_dashboard(user: User = Depends(teacher_user), db: Session = Depends(get_db)):
        if user.class_id is None:
            raise HTTPException(status_code=404, detail="Teacher is not assigned to a class")
        return dashboard_data(db, user.class_id)

    @app.get("/api/teacher/students")
    def teacher_students(user: User = Depends(teacher_user), db: Session = Depends(get_db)):
        students = db.scalars(select(User).where(User.class_id == user.class_id, User.role == "student").order_by(User.name))
        result = []
        for student in students:
            attempts = list(db.scalars(select(Submission).where(Submission.student_id == student.id)))
            result.append({
                "id": student.id,
                "name": student.name,
                "attempts": len(attempts),
                "accuracy": round(sum(x.is_correct for x in attempts) / len(attempts) * 100) if attempts else 0,
                "active_gaps": len({x.misconception_tag for x in attempts if x.misconception_tag}),
            })
        return result

    @app.post("/api/teacher/reteach", status_code=status.HTTP_201_CREATED)
    def reteach(payload: ReteachCreate, user: User = Depends(teacher_user), db: Session = Depends(get_db)):
        script = ai.reteach(payload.misconception_label, payload.affected_students)
        row = ReteachScript(
            teacher_id=user.id,
            class_id=user.class_id,
            misconception_tag=payload.misconception_tag,
            script=script,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return {"id": row.id, "misconception_tag": row.misconception_tag, "script": row.script, "created_at": row.created_at.isoformat()}

    return app


app = create_app()
