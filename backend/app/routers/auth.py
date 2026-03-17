from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, Token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=dict)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="郵箱已存在")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password, roles="user")
    db.add(db_user)
    db.commit()      # ← 確保這行存在！
    db.refresh(db_user)  # 重新載入 ID
    return {"msg": "註冊成功", "user_id": db_user.id}


@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="錯誤憑證")
    access_token = create_access_token(user.id, user.roles)
    return {"access_token": access_token, "token_type": "bearer"}
