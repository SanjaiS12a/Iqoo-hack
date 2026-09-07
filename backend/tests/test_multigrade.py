from pathlib import Path

from fastapi.testclient import TestClient

from .test_api import auth, login


def test_grade_registry_creates_physically_separate_databases(tmp_path: Path):
    from app.grade_database import GradeDatabaseRegistry

    registry = GradeDatabaseRegistry(tmp_path)
    registry.initialize(2)
    registry.initialize(9)

    assert (tmp_path / "classmind_grade_02.db").is_file()
    assert (tmp_path / "classmind_grade_09.db").is_file()
    assert registry.engine(2).url.database != registry.engine(9).url.database


def test_local_provider_selection_applies_to_assessment_and_tutoring():
    from app.ai import build_ai_provider

    provider = build_ai_provider("local", "local-model", "vision-model", "http://localhost:11434/v1")
    assert provider.__class__.__name__ == "CompatibleAssessmentProvider"


def test_application_initializes_all_twelve_grade_databases(client: TestClient):
    registry = client.app.state.grade_registry
    assert {path.name for path in registry.database_dir.glob("classmind_grade_*.db")} == {
        f"classmind_grade_{grade:02d}.db" for grade in range(1, 13)
    }


def test_teacher_lists_multiple_assigned_classes(client: TestClient):
    token = login(client, "meera@classmind.demo")
    response = client.get("/api/teacher/classes", headers=auth(token))

    assert response.status_code == 200
    assert {(item["grade"], item["section"]) for item in response.json()} >= {(9, "A"), (6, "B")}


def test_teacher_cannot_read_an_unassigned_class(client: TestClient):
    teacher_token = login(client, "meera@classmind.demo")
    admin_token = login(client, "admin@classmind.demo")
    classes = client.get("/api/admin/classes", headers=auth(admin_token)).json()
    unassigned = next(item for item in classes if item["grade"] == 2)

    response = client.get(f"/api/teacher/classes/{unassigned['id']}/dashboard", headers=auth(teacher_token))
    assert response.status_code == 403


def test_admin_moving_student_replaces_previous_class(client: TestClient):
    admin_token = login(client, "admin@classmind.demo")
    classes = client.get("/api/admin/classes", headers=auth(admin_token)).json()
    target = next(item for item in classes if item["grade"] == 6)
    users = client.get("/api/admin/users", headers=auth(admin_token)).json()
    student = next(item for item in users if item["email"] == "aarav@classmind.demo")

    moved = client.post(
        f"/api/admin/classes/{target['id']}/students/{student['id']}",
        headers=auth(admin_token),
    )
    assert moved.status_code == 200
    assert moved.json()["class_id"] == target["id"]

    profile = client.get("/api/auth/me", headers=auth(login(client, "aarav@classmind.demo")))
    assert profile.json()["class_id"] == target["id"]


def test_admin_can_create_section_without_internal_join_code(client: TestClient):
    admin_token = login(client, "admin@classmind.demo")

    created = client.post(
        "/api/admin/classes",
        headers=auth(admin_token),
        json={"grade": 1, "section": "A", "name": "Grade 1A", "subject": "General Studies"},
    )

    assert created.status_code == 201
    assert created.json()["grade"] == 1
    assert created.json()["section"] == "A"
    assert created.json()["join_code"]
