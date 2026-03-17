from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/profile")
def get_profile(current_user = Depends(get_current_user)):
    return current_user

@router.get("/admin")
def admin_panel(current_user = Depends(require_admin)):
    return {"message": "管理員專區", "user": current_user}
