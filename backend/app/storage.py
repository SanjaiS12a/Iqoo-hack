from pathlib import Path
from uuid import uuid4


ALLOWED_MEDIA = {
    "application/pdf": b"%PDF",
    "image/png": b"\x89PNG\r\n\x1a\n",
    "image/jpeg": b"\xff\xd8\xff",
}


def validate_upload(media_type: str, content: bytes, size_limit: int = 20 * 1024 * 1024) -> None:
    signature = ALLOWED_MEDIA.get(media_type)
    if signature is None or not content.startswith(signature):
        raise ValueError("Upload a genuine PDF, PNG, or JPEG file")
    if not content or len(content) > size_limit:
        raise ValueError("File must be between 1 byte and 20 MB")


class LocalPortionStorage:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def save(self, grade: int, class_id: int, original_filename: str, content: bytes) -> str:
        suffix = Path(original_filename).suffix.lower()
        destination = self.root / f"grade_{grade:02d}" / f"class_{class_id}"
        destination.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid4().hex}{suffix}"
        (destination / filename).write_bytes(content)
        return filename

