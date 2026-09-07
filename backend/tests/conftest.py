import os

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./classmind_test.db"
os.environ["AI_PROVIDER"] = "demo"
os.environ["JWT_SECRET"] = "test-secret-that-is-long-enough"

from app.main import create_app  # noqa: E402


@pytest.fixture()
def client(tmp_path, monkeypatch):
    database_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path.as_posix()}")
    app = create_app(database_url=f"sqlite:///{database_path.as_posix()}")
    with TestClient(app) as test_client:
        yield test_client
