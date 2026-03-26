from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])
SECURITY_SCHEMA = [{"bearer": []}]

@router.get("/profile", openapi_extra={"security": SECURITY_SCHEMA})
def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_admin": current_user.is_admin
    }

@router.get("/admin", openapi_extra={"security": SECURITY_SCHEMA})
def admin_panel(current_user: User = Depends(require_admin)):
    return {"message": "管理員專區", "user": current_user.email}