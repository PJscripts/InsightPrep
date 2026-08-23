from pathlib import Path
from uuid import uuid4

UPLOAD_DIR = Path("uploads/resumes")


def save_resume_file(content: bytes, extension: str) -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    stored_name = f"{uuid4()}{extension}"
    file_path = UPLOAD_DIR / stored_name

    file_path.write_bytes(content)

    return file_path


def delete_resume_file(file_path: str) -> None:
    Path(file_path).unlink(missing_ok=True)
