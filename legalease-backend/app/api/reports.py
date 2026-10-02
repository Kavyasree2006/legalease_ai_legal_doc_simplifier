from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Analysis, Document, User
from app.services.report import generate_report

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/{document_id}/download")
def download_report(document_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.scalar(select(Document).options(selectinload(Document.analyses).selectinload(Analysis.risk_clauses)).where(Document.id == document_id, Document.user_id == user.id))
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    analysis = max(doc.analyses, key=lambda a: a.id, default=None)
    if not analysis or analysis.status != "completed":
        raise HTTPException(status_code=409, detail="The analysis is not complete yet")
    path = Path(generate_report(doc, analysis))
    return FileResponse(path, media_type="application/pdf", filename=f"{Path(doc.filename).stem}-LegalEase-Report.pdf")
