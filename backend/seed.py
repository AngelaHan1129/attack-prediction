import os
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash


def seed_data():
    if not os.path.exists("data"):
        os.makedirs("data")
        print("✅ 已建立 data 資料夾")

    db: Session = SessionLocal()

    try:
        admin_email = "admin@example.com"
        admin_username = "admin"

        user = db.query(User).filter(User.email == admin_email).first()

        if not user:
            print(f"正在建立預設管理員: {admin_email}")
            new_admin = User(
                username="admin",
                email=admin_email,
                hashed_password=get_password_hash("Admin123!@#"),
                is_admin=True,
                is_active=True,
                email_verified=True,
                failed_login_count=0,
            )
            db.add(new_admin)
            db.commit()
            db.refresh(new_admin)
            print("🚀 管理員帳號建立成功！")
        else:
            print("ℹ️ 管理員帳號已存在，跳過建立。")

    except Exception as e:
        db.rollback()
        print(f"❌ 發生錯誤: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()