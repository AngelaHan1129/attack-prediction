import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage

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
    ResendVerificationRequest,
    TokenResponse,
    VerifyEmailRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])

INVALID_LOGIN_MESSAGE = "帳號或密碼錯誤"


def send_verification_email(email: str, token: str) -> None:
    print("[EMAIL] prepare verification email to=", email)
    verify_link = f"{settings.FRONTEND_VERIFY_URL}?token={token}"

    msg = EmailMessage()
    msg["Subject"] = "[Obelisk Security] Email 驗證信"
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM}>"
    msg["To"] = email

    msg.set_content(
        f"請點擊以下連結完成 Email 驗證：\n{verify_link}\n\n"
        "如果這不是你本人操作，請忽略此信件。"
    )

    msg.add_alternative(
        f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2>歡迎加入系統</h2>
            <p>請點擊下方連結完成 Email 驗證：</p>
            <p><a href="{verify_link}">{verify_link}</a></p>
            <p>如果這不是你本人操作，請忽略此信件。</p>
          </body>
        </html>
        """,
        subtype="html",
    )

    try:
        print(f"[EMAIL] sending verification email to {email}")

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
            server.set_debuglevel(1)
            server.ehlo()

            if settings.SMTP_USE_TLS:
                server.starttls()
                server.ehlo()

            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)

        print(f"[EMAIL] verification email sent to {email}")

    except smtplib.SMTPAuthenticationError as e:
        print("SMTPAuthenticationError:", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gmail 驗證失敗，請檢查 App Password、Gmail 帳號與兩步驟驗證設定",
        )
    except smtplib.SMTPException as e:
        print("SMTPException:", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SMTP 寄信失敗：{str(e)}",
        )
    except Exception as e:
        print("General email error:", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"寄信失敗：{str(e)}",
        )


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing_username = db.query(User).filter(User.username == payload.username).first()
    print("[REGISTER] payload:", payload.username, payload.email)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="使用者名稱已被使用",
        )

    existing_email = db.query(User).filter(User.email == payload.email).first()
    if existing_email:
        if existing_email.email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="電子郵件已被註冊",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此電子郵件已註冊但尚未完成驗證，請改用重寄驗證信功能",
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

    try:
        db.add(user)
        db.commit()
        db.refresh(user)

        verification_token = create_email_verification_token(str(user.id))
        user.verification_token = verification_token
        db.commit()

        send_verification_email(user.email, verification_token)

        return {"message": "註冊成功，請至信箱完成驗證後登入"}

    except HTTPException:
        if user.id:
            db.delete(user)
            db.commit()
        raise
    except Exception as e:
        print("Register error:", e)
        if user.id:
            db.delete(user)
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="註冊失敗，請稍後再試",
        )


@router.post("/resend-verification")
def resend_verification(payload: ResendVerificationRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="找不到此電子郵件對應的帳號",
        )

    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此帳號已完成 Email 驗證",
        )

    verification_token = create_email_verification_token(str(user.id))
    user.verification_token = verification_token
    db.commit()

    send_verification_email(user.email, verification_token)

    return {"message": "驗證信已重新寄出，請至信箱查收"}


@router.post("/register/admin")
def register_admin(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing_username = db.query(User).filter(User.username == payload.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="使用者名稱已被使用",
        )

    existing_email = db.query(User).filter(User.email == payload.email).first()
    if existing_email:
        if existing_email.email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="電子郵件已被註冊",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此電子郵件已註冊但尚未完成驗證，請改用重寄驗證信功能",
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