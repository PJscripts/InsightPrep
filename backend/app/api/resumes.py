import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.settings import settings
from app.models.resume import Resume
from app.models.user import User
from app.services.analyzer_factory import get_resume_analyzer
from app.services.file_storage import delete_resume_file, save_resume_file
from app.services.resume_extractor import extract_resume_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resumes", tags=["Resumes"])

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE = 5 * 1024 * 1024


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    extension = Path(file.filename or "").suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are supported",
        )

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be 5 MB or less",
        )

    file_path = save_resume_file(content, extension)

    try:
        extracted_text = extract_resume_text(str(file_path))

        analyzer = get_resume_analyzer()

        try:
            analysis = analyzer.analyze(extracted_text)

        except Exception:
            fallback_provider = settings.resume_fallback_llm.lower()

            if fallback_provider == "groq":
                try:
                    from app.services.groq_resume_analyzer import (
                        GroqResumeAnalyzer,
                    )

                    fallback_analyzer = GroqResumeAnalyzer()
                    analysis = fallback_analyzer.analyze(extracted_text)

                except Exception:
                    from app.services.mock_resume_analyzer import (
                        MockResumeAnalyzer,
                    )

                    analysis = MockResumeAnalyzer().analyze(
                        extracted_text,
                    )

            elif fallback_provider == "mock":
                from app.services.mock_resume_analyzer import (
                    MockResumeAnalyzer,
                )

                analysis = MockResumeAnalyzer().analyze(
                    extracted_text,
                )

            else:
                raise

    except Exception as exc:
        logger.exception("Failed to process resume")

        delete_resume_file(str(file_path))

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not process the resume",
        ) from exc

    resume = Resume(
        user_id=current_user.id,
        file_name=file.filename or file_path.name,
        file_type=extension,
        file_path=str(file_path),
        extracted_text=extracted_text,
        analysis_status="analyzed",
        analysis=analysis,
    )

    try:
        db.add(resume)
        db.commit()
        db.refresh(resume)
    except Exception as exc:
        db.rollback()
        delete_resume_file(str(file_path))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save the processed resume",
        ) from exc

    return {
        "id": resume.id,
        "file_name": resume.file_name,
        "file_type": resume.file_type,
        "analysis_status": resume.analysis_status,
        "text_length": len(extracted_text),
        "analysis": resume.analysis,
    }


@router.get("/profile")
def get_resume_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = db.scalar(
        select(Resume)
        .where(
            Resume.user_id == current_user.id,
            Resume.analysis_status == "analyzed",
        )
        .order_by(Resume.created_at.desc())
    )

    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analyzed resume found",
        )

    return {
        "resume_id": resume.id,
        "file_name": resume.file_name,
        "analysis": resume.analysis,
    }
