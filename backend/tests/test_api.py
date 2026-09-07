from fastapi.testclient import TestClient


def login(client: TestClient, email: str, password: str = "demo1234") -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_demo_users_can_login_and_invalid_credentials_are_rejected(client: TestClient):
    student = client.post(
        "/api/auth/login",
        json={"email": "aarav@classmind.demo", "password": "demo1234"},
    )
    assert student.status_code == 200
    assert student.json()["user"]["role"] == "student"

    invalid = client.post(
        "/api/auth/login",
        json={"email": "aarav@classmind.demo", "password": "wrong"},
    )
    assert invalid.status_code == 401


def test_student_submission_is_diagnosed_and_visible_to_teacher(client: TestClient):
    student_token = login(client, "aarav@classmind.demo")
    questions = client.get("/api/student/questions", headers=auth(student_token)).json()
    question = next(q for q in questions if q["slug"] == "linear-sign-demo")

    result = client.post(
        "/api/student/submissions",
        headers=auth(student_token),
        json={"question_id": question["id"], "answer_text": "2x = 10 - 4, so x = 7"},
    )
    assert result.status_code == 201
    assert result.json()["is_correct"] is False
    assert result.json()["misconception_tag"] == "sign_error_transposition"

    teacher_token = login(client, "meera@classmind.demo")
    dashboard = client.get("/api/teacher/dashboard", headers=auth(teacher_token))
    assert dashboard.status_code == 200
    matching = [x for x in dashboard.json()["misconceptions"] if x["tag"] == "sign_error_transposition"]
    assert matching
    assert matching[0]["affected_students"] >= 1


def test_roles_cannot_access_each_others_endpoints(client: TestClient):
    student_token = login(client, "aarav@classmind.demo")
    teacher_token = login(client, "meera@classmind.demo")
    assert client.get("/api/teacher/dashboard", headers=auth(student_token)).status_code == 403
    assert client.get("/api/student/overview", headers=auth(teacher_token)).status_code == 403


def test_doubt_is_logged_and_returns_conceptual_help(client: TestClient):
    token = login(client, "aarav@classmind.demo")
    response = client.post(
        "/api/student/doubts",
        headers=auth(token),
        json={"doubt_text": "Why does a minus sign change when I move a term?"},
    )
    assert response.status_code == 201
    assert response.json()["concept_tag"] == "transposition"
    assert "balance" in response.json()["ai_response"].lower()


def test_study_plan_prioritizes_active_high_weight_weakness_and_can_complete_item(client: TestClient):
    token = login(client, "aarav@classmind.demo")
    response = client.post("/api/student/study-plan/generate", headers=auth(token))
    assert response.status_code == 201
    items = response.json()["items"]
    assert len(items) >= 3
    assert items[0]["priority_score"] >= items[1]["priority_score"]

    updated = client.patch(
        f"/api/student/study-plan/items/{items[0]['id']}",
        headers=auth(token),
        json={"completed": True},
    )
    assert updated.status_code == 200
    assert updated.json()["completed"] is True


def test_teacher_can_generate_reteach_script(client: TestClient):
    token = login(client, "meera@classmind.demo")
    response = client.post(
        "/api/teacher/reteach",
        headers=auth(token),
        json={
            "misconception_tag": "sign_error_transposition",
            "misconception_label": "Sign error while moving terms",
            "affected_students": 12,
        },
    )
    assert response.status_code == 201
    assert "12" in response.json()["script"]
    assert response.json()["misconception_tag"] == "sign_error_transposition"
