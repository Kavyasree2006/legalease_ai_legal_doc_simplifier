from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, documents, analysis, history, reports, settings
from app.core.config import get_settings
from app.db.session import Base, engine
from app.models import User, Document, Analysis, RiskClause  # noqa: F401

settings_config = get_settings()
Path(settings_config.upload_dir).mkdir(parents=True, exist_ok=True)
Path(settings_config.report_dir).mkdir(parents=True, exist_ok=True)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings_config.app_name, version="1.0.0", description="LegalEase AI-powered legal document analysis backend")
app.add_middleware(CORSMiddleware, allow_origins=settings_config.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(settings.router, prefix="/api")

@app.get("/")
def root():
    return {"name": "LegalEase API", "status": "ok", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok"}
