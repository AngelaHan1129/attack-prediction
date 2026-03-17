# ATTACK-PREDICTION Backend - FastAPI + YOLO 部署指南

## 🚀 快速啟動（5 分鐘）

### 1. 虛擬環境建立
```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate  # 顯示 (.venv) 前綴
```

### 2. 安裝依賴（修復版本衝突）
```powershell
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```
**重要**：若 `bcrypt` 錯誤執行：
```powershell
pip uninstall bcrypt passlib -y
pip install "bcrypt==4.0.1" "passlib[bcrypt]==1.7.4" --force-reinstall
```

### 3. 資料庫初始化（SQLite 自動）
```powershell
# 第一次執行，自動產生 app.db
uvicorn app.main:app --host 127.0.0.1 --port 8000
```
按 `Ctrl+C` 停止。

### 4. Alembic 遷移（版本控制）
```powershell
alembic init alembic
# 編輯 alembic/env.py 第95行：target_metadata = Base.metadata
alembic revision --autogenerate -m "init users"
alembic upgrade head
```

### 5. 啟動開發伺服器
```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
✅ **成功**：`Application startup complete`

## 🔍 API 測試（Swagger）
瀏覽 **http://127.0.0.1:8000/docs**

```
1. POST /auth/register → {"email":"admin@test.com","password":"admin123"}
2. POST /auth/token → {"username":"admin@test.com","password":"admin123"}
3. GET /users/profile → Headers: Authorization: Bearer {token}
4. GET /users/admin → 僅 admin 權限
```

## 📁 專案結構
```
backend/
├── app/                 # FastAPI 核心
│   ├── core/           # 配置、安全、依賴
│   ├── models/         # SQLAlchemy 模型
│   ├── routers/        # API 路由
│   ├── schemas/        # Pydantic 驗證
│   └── database/       # DB session
├── services/           # YOLO 模型 (camera.py, detect.py, yolo26n.pt)
├── alembic/            # 資料庫遷移
├── app.db             # SQLite 資料庫
├── alembic.ini
├── requirements.txt
└── .env               # DATABASE_URL=sqlite:///./app.db
```

## 🛠️ 常見問題修復

### ❌ bcrypt 錯誤 `(trapped) error reading bcrypt version`
```powershell
pip install "bcrypt==4.0.1" --force-reinstall
```

### ❌ multiprocessing Windows 錯誤
```powershell
uvicorn app.main:app --reload --no-use-colors
```

### ❌ NameError: name 'Field' is not defined
**app/schemas/user.py** 第一行加：
```python
from pydantic import BaseModel, EmailStr, Field
```

### ❌ 資料庫未建立
刪除 `app.db`，重啟 uvicorn（自動重建）。

## 🔗 前端 React 整合
**package.json**：
```json
"proxy": "http://127.0.0.1:8000"
```
**axios 設定**：
```javascript
const api = axios.create({ baseURL: '/api' });  // proxy 自動轉發
```

## 🚀 生產部署（Docker）
```bash
docker-compose up -d
```

## 📊 YOLO 整合
```
services/
├── camera.py
├── detect.py
├── YOLO-download.py
└── models/
    └── yolo26n.pt
```
新增 **app/routers/yolo.py**，`main.py` include_router。

## 👥 團隊協作
```powershell
git add .
git commit -m "feat: complete FastAPI + RBAC + YOLO backend"
git push origin main
```
