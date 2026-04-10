from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    ALGORITHM,
    create_access_token,
    create_email_verification_token,
    create_refresh_token,
    get_password_hash,
    validate_password_strength,
    verify_password,
)
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    VerifyEmailRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])

INVALID_LOGIN_MESSAGE = "帳號或密碼錯誤"


def send_verification_email(email: str, token: str) -> None:
    verify_link = f"{settings.FRONTEND_VERIFY_URL}?token={token}"
    print(f"[VERIFY EMAIL] to={email} link={verify_link}")


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(
        or_(User.username == payload.username, User.email == payload.email)
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="帳號資料無法使用",
        )

    try:
        validate_password_strength(payload.password, payload.username, payload.email)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    hashed_password = get_password_hash(payload.password)

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=False,
        email_verified=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    verification_token = create_email_verification_token(str(user.id))
    user.verification_token = verification_token
    db.commit()

    send_verification_email(user.email, verification_token)

    return {"message": "註冊成功，請至信箱完成驗證後登入"}


@router.post("/register/admin")
def register_admin(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(
        or_(User.username == payload.username, User.email == payload.email)
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="帳號資料無法使用",
        )

    try:
        validate_password_strength(payload.password, payload.username, payload.email)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    hashed_password = get_password_hash(payload.password)

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=True,
        email_verified=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    verification_token = create_email_verification_token(str(user.id))
    user.verification_token = verification_token
    db.commit()

    send_verification_email(user.email, verification_token)

    return {"message": "管理員註冊成功，請完成 Email 驗證", "user_id": user.id}


@router.post("/verify-email")
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    try:
        decoded = jwt.decode(
            payload.token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        token_type = decoded.get("type")
        user_id = decoded.get("sub")

        if token_type != "email_verification" or not user_id:
            raise ValueError()
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="驗證連結無效或已過期",
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="驗證連結無效或已過期",
        )

    if user.verification_token != payload.token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="驗證連結無效或已過期",
        )

    user.email_verified = True
    user.verification_token = None
    db.commit()

    return {"message": "Email 驗證成功，現在可以登入"}


def _issue_tokens_for_user(user: User, db: Session) -> TokenResponse:
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    user.refresh_token = refresh_token
    user.failed_login_count = 0
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


def _authenticate_user(username_or_email: str, password: str, db: Session) -> User:
    user = db.query(User).filter(
        or_(
            User.username == username_or_email,
            User.email == username_or_email,
        )
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_LOGIN_MESSAGE,
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(password, user.hashed_password):
        user.failed_login_count = (user.failed_login_count or 0) + 1
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_LOGIN_MESSAGE,
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="帳號已停用，請聯絡管理員",
        )

    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="請先完成 Email 驗證",
        )

    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = _authenticate_user(payload.username_or_email, payload.password, db)
    return _issue_tokens_for_user(user, db)


@router.post("/token", response_model=TokenResponse)
def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = _authenticate_user(form_data.username, form_data.password, db)
    return _issue_tokens_for_user(user, db)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    try:
        decoded = jwt.decode(
            payload.refresh_token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        token_type = decoded.get("type")
        user_id = decoded.get("sub")

        if token_type != "refresh" or not user_id:
            raise ValueError()
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token 無效或已過期",
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or user.refresh_token != payload.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token 無效或已過期",
        )

    new_access_token = create_access_token(str(user.id))
    new_refresh_token = create_refresh_token(str(user.id))

    user.refresh_token = new_refresh_token
    db.commit()

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
    )