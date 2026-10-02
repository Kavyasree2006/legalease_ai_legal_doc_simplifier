from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models import Analysis, Document, User
from app.services.analysis_runner import run_analysis
from app.services.extractor import extract_text
from app.services.serializers import analysis_dict, document_dict

router = APIRouter(prefix="/documents", tags=["Documents"])
ALLOWED = {".pdf", ".docx"}


def _owned_document(db: Session, user: User, document_id: int) -> Document:
    doc = db.scalar(select(Document).options(selectinload(Document.analyses).selectinload(Analysis.risk_clauses)).where(Document.id == document_id, Document.user_id == user.id))
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.get("")
def list_documents(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    docs = db.scalars(select(Document).options(selectinload(Document.analyses)).where(Document.user_id == user.id).order_by(Document.created_at.desc())).unique().all()
    return [document_dict(d) for d in docs]

@router.get("/{document_id}")
def get_document(document_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = _owned_document(db, user, document_id)
    data = document_dict(doc, include_text=False)
    latest = max(doc.analyses, key=lambda a: a.id, default=None)
    data["analysis"] = analysis_dict(latest) if latest else None
    return data

@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    settings = get_settings()
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(status_code=415, detail="Only PDF and DOCX files are supported")
    content = file.file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds the {settings.max_upload_size_mb} MB limit")
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}{suffix}"
    path = upload_dir / stored_name
    path.write_bytes(content)

    try:
        text, _ = extract_text(str(path), file.filename or stored_name)
    except Exception as exc:
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Could not extract text from the document: {exc}") from exc
    if not text.strip():
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="No readable text was found in the document. For scanned PDFs, install Tesseract OCR and try again.")

    document = Document(user_id=user.id, filename=file.filename or stored_name, file_type=file.content_type or "application/octet-stream", file_size=len(content), file_path=str(path), extracted_text=text, status="queued")
    db.add(document); db.flush()
    analysis = Analysis(document_id=document.id, status="pending")
    db.add(analysis); db.commit(); db.refresh(document); db.refresh(analysis)
    background_tasks.add_task(run_analysis, analysis.id)
    return {"document_id": document.id, "analysis_id": analysis.id, "document": document_dict(document), "analysis": {"id": analysis.id, "status": analysis.status}}

@router.delete("/{document_id}")
def delete_document(document_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = _owned_document(db, user, document_id)
    path = Path(doc.file_path)
    db.delete(doc); db.commit()
    path.unlink(missing_ok=True)
    return {"message": "Document deleted"}
