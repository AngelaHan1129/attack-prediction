from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.database.session import get_db
from app.core.config import settings
from app.core.security import ALGORITHM
from app.models.user import User

# 指向登入取得 token 的 API 路徑
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def get_current_user(
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    驗證 JWT Token 並從資料庫回傳 User 物件
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token 無效或已過期",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 1. 解碼 Token (使用與 security.py 相同的 SECRET_KEY)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        
        # 2. 取得 sub (這是你在 create_access_token 存入的 user.id)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception

    # 3. 關鍵修正：根據 ID 查詢，而非 Email (因為你的 sub 存的是 ID)
    user = db.query(User).filter(User.id == int(user_id)).first()
    
    if user is None:
        raise credentials_exception
        
    return user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    檢查使用者是否具備管理員權限
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="權限不足，僅限管理員執行此操作"
        )
    return current_user