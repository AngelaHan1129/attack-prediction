from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])
SECURITY_SCHEMA = [{"bearer": []}]


@router.get("/profile", openapi_extra={"security": SECURITY_SCHEMA})
def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "email_verified": current_user.email_verified,
        "is_active": current_user.is_active,
        "is_admin": current_user.is_admin,
        "last_login_at": current_user.last_login_at,
        "created_at": current_user.created_at,
    }


@router.get("/admin", openapi_extra={"security": SECURITY_SCHEMA})
def admin_panel(current_user: User = Depends(require_admin)):
    return {
        "message": "管理員專區",
        "user": current_user.email,
        "role": "admin",
    }