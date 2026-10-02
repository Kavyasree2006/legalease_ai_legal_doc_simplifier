from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Analysis, Document, User
from app.schemas.common import AnalyzeRequest
from app.services.analysis_runner import run_analysis
from app.services.serializers import analysis_dict

router = APIRouter(prefix="/analysis", tags=["Analysis"])


def _analysis(db: Session, user: User, analysis_id: int):
    return db.scalar(select(Analysis).join(Document).options(selectinload(Analysis.risk_clauses)).where(Analysis.id == analysis_id, Document.user_id == user.id))

@router.get("/{analysis_id}")
def get_analysis(analysis_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    analysis = _analysis(db, user, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis_dict(analysis)

@router.get("/document/{document_id}")
def get_document_analysis(document_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    analysis = db.scalar(select(Analysis).join(Document).options(selectinload(Analysis.risk_clauses)).where(Analysis.document_id == document_id, Document.user_id == user.id).order_by(Analysis.id.desc()))
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis_dict(analysis)

@router.post("/analyze")
def analyze_document(payload: AnalyzeRequest, background_tasks: BackgroundTasks, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    document = db.scalar(select(Document).where(Document.id == payload.document_id, Document.user_id == user.id))
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    analysis = db.scalar(select(Analysis).where(Analysis.document_id == document.id).order_by(Analysis.id.desc()))
    if not analysis:
        analysis = Analysis(document_id=document.id, status="pending")
        db.add(analysis); db.commit(); db.refresh(analysis)
    elif analysis.status in {"failed", "completed"}:
        analysis.status = "pending"; analysis.error_message = None; db.commit()
    background_tasks.add_task(run_analysis, analysis.id)
    return analysis_dict(analysis)
