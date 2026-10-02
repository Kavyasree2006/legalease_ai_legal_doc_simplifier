from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.common import SettingsUpdate
from app.services.serializers import user_dict

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("")
def get_settings(user: User = Depends(get_current_user)):
    return user_dict(user)

@router.patch("")
def update_settings(payload: SettingsUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.name = payload.name.strip()
    db.commit(); db.refresh(user)
    return user_dict(user)
