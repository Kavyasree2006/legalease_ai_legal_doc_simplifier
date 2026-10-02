from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Analysis, Document, User
from app.services.serializers import document_dict

router = APIRouter(prefix="/history", tags=["History"])

@router.get("")
def history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    docs = db.scalars(select(Document).options(selectinload(Document.analyses)).where(Document.user_id == user.id).order_by(Document.created_at.desc())).unique().all()
    return [document_dict(d) for d in docs]
