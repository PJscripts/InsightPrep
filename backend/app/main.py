from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.resumes import router as resumes_router
from app.core.settings import settings

app = FastAPI(
    title=settings.app_name,
    description="LLM-powered technical interview preparation platform",
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(resumes_router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AI Interview Assessment System",
    }
