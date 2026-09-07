from contextlib import contextmanager
from pathlib import Path
from threading import Lock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .academic_models import AcademicBase


class GradeDatabaseRegistry:
    def __init__(self, database_dir: str | Path, url_template: str | None = None):
        self.database_dir = Path(database_dir)
        self.url_template = url_template
        self._engines: dict[int, object] = {}
        self._factories: dict[int, sessionmaker] = {}
        self._lock = Lock()

    @staticmethod
    def validate_grade(grade: int) -> int:
        if grade < 1 or grade > 12:
            raise ValueError("Grade must be between 1 and 12")
        return grade

    def _url(self, grade: int) -> str:
        self.validate_grade(grade)
        if self.url_template:
            return self.url_template.format(grade=grade, grade_padded=f"{grade:02d}")
        self.database_dir.mkdir(parents=True, exist_ok=True)
        path = (self.database_dir / f"classmind_grade_{grade:02d}.db").resolve()
        return f"sqlite:///{path.as_posix()}"

    def engine(self, grade: int):
        grade = self.validate_grade(grade)
        if grade not in self._engines:
            with self._lock:
                if grade not in self._engines:
                    url = self._url(grade)
                    args = {"check_same_thread": False} if url.startswith("sqlite") else {}
                    engine = create_engine(url, connect_args=args)
                    self._engines[grade] = engine
                    self._factories[grade] = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
        return self._engines[grade]

    def initialize(self, grade: int) -> None:
        AcademicBase.metadata.create_all(self.engine(grade))

    @contextmanager
    def session(self, grade: int):
        self.initialize(grade)
        with self._factories[grade]() as session:
            yield session

    def dispose(self) -> None:
        for engine in self._engines.values():
            engine.dispose()

