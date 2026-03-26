from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
# 確保路徑正確引入
from app.routers import auth, users, yolo 

# 1. 建立 FastAPI 實例，變數名必須是 app
app = FastAPI(title="Attack Prediction API")

# 2. 註冊所有路由
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(yolo.router)

# 3. 自定義 OpenAPI Schema (讓 Swagger 顯示 Authorize 鎖頭)
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Attack Prediction API",
        version="1.0.0",
        description="結合 YOLO 的攻擊意圖預測系統",
        routes=app.routes,
    )
    
    # 確保 components 鍵存在
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    
    # 定義 Security Scheme
    openapi_schema["components"]["securitySchemes"] = {
        "bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "請輸入 JWT Token（不需要加 Bearer 前綴）"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# 將自定義函式掛載
app.openapi = custom_openapi

# (可選) 根目錄測試
@app.get("/")
async def root():
    return {"message": "Backend API is running"}