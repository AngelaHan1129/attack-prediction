import os
from sqlalchemy.orm import Session
from app.database.session import SessionLocal, engine, Base
from app.models.user import User
from app.core.security import get_password_hash

def seed_data():
    # 1. 確保 data 目錄存在 (對應你的 config.py)
    if not os.path.exists("data"):
        os.makedirs("data")
        print("✅ 已建立 data 資料夾")

    # 2. 強制建立所有資料表 (如果還沒建立的話)
    print("正在初始化資料庫資料表...")
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # 3. 檢查管理員是否已存在
        admin_email = "admin@example.com"
        user = db.query(User).filter(User.email == admin_email).first()

        if not user:
            print(f"正在建立預設管理員: {admin_email}")
            new_admin = User(
                email=admin_email,
                hashed_password=get_password_hash("admin123"), # 密碼是 admin123
                is_admin=True,
                is_active=True
            )
            db.add(new_admin)
            db.commit()
            print("🚀 管理員帳號建立成功！")
        else:
            print("ℹ️ 管理員帳號已存在，跳過建立。")

    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()