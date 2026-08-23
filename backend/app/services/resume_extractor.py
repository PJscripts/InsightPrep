from pathlib import Path

from docx import Document
from pypdf import PdfReader


def extract_pdf_text(file_path: str) -> str:
    reader = PdfReader(file_path)

    pages = []

    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)

    return "\n".join(pages).strip()


def extract_docx_text(file_path: str) -> str:
    document = Document(file_path)

    paragraphs = [paragraph.text for paragraph in document.paragraphs]

    return "\n".join(paragraphs).strip()


def extract_resume_text(file_path: str) -> str:
    extension = Path(file_path).suffix.lower()

    if extension == ".pdf":
        return extract_pdf_text(file_path)

    if extension == ".docx":
        return extract_docx_text(file_path)

    raise ValueError("Unsupported resume file type")
