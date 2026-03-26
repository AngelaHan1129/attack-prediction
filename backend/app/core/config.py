from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # 如果 .env 沒設定，則使用預設值
    DATABASE_URL: str = Field(default="sqlite:///./data/app.db")
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 關鍵：指定讀取 backend/.env 檔案
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore" # 忽略 .env 中多餘的變數
    )

settings = Settings()

