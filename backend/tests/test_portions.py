from fastapi.testclient import TestClient

from .test_api import auth, login


PNG = b"\x89PNG\r\n\x1a\n" + b"classmind-demo-image"


def teacher_class(client: TestClient, token: str, grade: int = 9) -> dict:
    classes = client.get("/api/teacher/classes", headers=auth(token)).json()
    return next(item for item in classes if item["grade"] == grade)


def test_teacher_uploads_draft_edits_and_publishes_portion(client: TestClient):
    token = login(client, "meera@classmind.demo")
    classroom = teacher_class(client, token)
    uploaded = client.post(
        f"/api/teacher/classes/{classroom['id']}/portions",
        headers=auth(token),
        files={"file": ("linear-equations.png", PNG, "image/png")},
    )
    assert uploaded.status_code == 201
    draft = uploaded.json()
    assert draft["status"] == "draft"
    assert draft["topics"]
    assert draft["questions"]

    updated = client.put(
        f"/api/teacher/classes/{classroom['id']}/portions/{draft['id']}",
        headers=auth(token),
        json={
            "title": "Term 1 · Linear Equations",
            "subject": "Mathematics",
            "topics": [{"title": "Balancing equations", "learning_outcome": "Solve one-variable equations", "sequence": 1}],
            "questions": [{"text": "Solve x + 4 = 9", "expected_answer": "x = 5", "difficulty": "Foundation", "topic": "Balancing equations", "exam_weight": 0.8}],
        },
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Term 1 · Linear Equations"

    published = client.post(
        f"/api/teacher/classes/{classroom['id']}/portions/{draft['id']}/publish",
        headers=auth(token),
    )
    assert published.status_code == 200
    assert published.json()["status"] == "published"


def test_upload_rejects_content_that_does_not_match_allowed_file_signature(client: TestClient):
    token = login(client, "meera@classmind.demo")
    classroom = teacher_class(client, token)
    response = client.post(
        f"/api/teacher/classes/{classroom['id']}/portions",
        headers=auth(token),
        files={"file": ("fake.pdf", b"not a pdf", "application/pdf")},
    )
    assert response.status_code == 415


def test_student_questions_and_plan_use_published_section_portion(client: TestClient):
    teacher_token = login(client, "meera@classmind.demo")
    classroom = teacher_class(client, teacher_token)
    draft = client.post(
        f"/api/teacher/classes/{classroom['id']}/portions",
        headers=auth(teacher_token),
        files={"file": ("fractions.png", PNG, "image/png")},
    ).json()
    client.post(
        f"/api/teacher/classes/{classroom['id']}/portions/{draft['id']}/publish",
        headers=auth(teacher_token),
    )

    student_token = login(client, "aarav@classmind.demo")
    questions = client.get("/api/student/questions", headers=auth(student_token))
    assert questions.status_code == 200
    assert questions.json()
    assert {item["portion_id"] for item in questions.json()} == {draft["id"]}

    plan = client.post("/api/student/study-plan/generate", headers=auth(student_token))
    assert plan.status_code == 201
    portion_topics = {item["title"] for item in draft["topics"]}
    assert {item["topic"] for item in plan.json()["items"]} <= portion_topics
