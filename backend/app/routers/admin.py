from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])

@router.put("/users/{user_id}/role")
async def set_admin_role(
    user_id: int, 
    new_role: str = "admin",
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用戶不存在")
    user.roles = new_role
    db.commit()
    db.refresh(user)
    return {"msg": f"用戶 {user.email} 權限更新為 {new_role}"}
