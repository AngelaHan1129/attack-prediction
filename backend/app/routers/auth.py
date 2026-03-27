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
    db_user = User(
    email=user.email, 
    hashed_password=hashed_password, 
    is_admin=False  # 使用你模型中定義的欄位名
)
    db.add(db_user)
    db.commit()      # ← 確保這行存在！
    db.refresh(db_user)  # 重新載入 ID
    return {"msg": "註冊成功", "user_id": db_user.id}

@router.post("/register/admin", response_model=dict)
def register_admin(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="郵箱已存在")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        is_admin=True  # ← 直接設為 admin
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"msg": "管理員註冊成功", "user_id": db_user.id}

@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. 查找使用者
    user = db.query(User).filter(User.email == form_data.username).first()
    
    # 2. 驗證使用者是否存在且密碼正確
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="電子郵件或密碼錯誤",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. 根據 is_admin 決定角色字串 (給 Token 使用)
    user_role = "admin" if user.is_admin else "user"
    
    # 4. 產生 Access Token (將 ID 轉為字串比較保險)
    access_token = create_access_token(
        subject=user.id, 
        roles=user_role
    )
    
    return {"access_token": access_token, "token_type": "bearer"}