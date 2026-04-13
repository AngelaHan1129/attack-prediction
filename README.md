# 🚨 攻擊意圖預測系統


## ✨ 功能特色

- 🖥️ **戰情儀表板**：12路即時監視 + L0-L4風險色碼
- 🚨 **即時告警**：WebSocket <1s 推播 L3/L4 高風險
- 📊 **AI 分析**：YOLO26偵測 + ByteTrack追蹤 + ST-GCN/LSTM預測
- 🔍 **智慧檢索**：RAG + Milvus 相似歷史案例比對
- 📱 **響應式設計**：Desktop/Tablet/Mobile 全適配
- 🔐 **權限管理**：維安人員/場域主管/系統管理員

## 🏗️ 技術堆疊

```
前端: React 18 + Vite + TypeScript + Tailwind + React Query
後端: FastAPI 0.104 + SQLAlchemy + Pydantic
AI:   YOLO26 + ByteTrack + MediaPipe + ST-GCN + LSTM
資料庫: PostgreSQL + Milvus + Redis + MinIO
部署: Docker Compose + Nginx + Gunicorn/Uvicorn
```

## 🚀 快速啟動

### 前置條件
```bash
# 安裝 Docker + Docker Compose
# GPU 驅動 (NVIDIA CUDA 12+)
# Node.js 18+
# Python 3.11+
```

### 一鍵部署
```bash
# 1. 複製環境設定
cp .env.example .env

# 2. 啟動所有服務
docker-compose up -d

# 3. 初始化資料庫
docker-compose exec backend alembic upgrade head

# 4. 載入初始資料
docker-compose exec backend python scripts/seed-data.py
```

### 存取介面
```
戰情儀表板: http://localhost:3000
API 文件:   http://localhost:8000/docs
後台管理:   http://localhost:3000/admin (admin/admin)
預設帳號:
- 維安人員: officer/officer (車站A)
- 管理員:   admin/admin
```

***

## 📋 專案結構

```
attack-prediction/
├── backend/                 # FastAPI API + ML核心
│   ├── main.py             # 🚀 API入口
│   ├── api/                # 📡 路由模組
│   ├── core/               # 🤖 YOLO26/ST-GCN/RAG
│   ├── db/                 # 🗄️ PostgreSQL/Milvus
│   └── models/             # 📋 Pydantic Schema
├── frontend/                # React 前端
│   ├── src/
│   │   ├── components/     # 🎨 CameraTile/AlertCard
│   │   ├── pages/          # 📄 Dashboard/EventDetail
│   │   └── hooks/          # 🔗 useEvents/useWebSocket
├── docker-compose.yml      # 🐳 一鍵部署
└── .env.example            # ⚙️ 環境變數
```

***

## 🔧 使用說明

### 戰情儀表板功能
```
左側: 12路即時監視 (點擊全螢幕)
右側: 即時告警列表 (一鍵處理/升級)
頂部: 今日統計 + 場域切換
```

### 事件詳情頁功能
```
🎥 事件回放 (前10s+後10s)
📈 風險曲線圖 (時間vs分數)
🎯 X1-X9雷達圖 (九大前兆指標)
🔍 RAG相似案例 (92%相似台北車站案)
✅ 狀態更新 (已處理/升級/忽略)
```

### 後台管理功能
```
👥 使用者管理 (角色/場域權限)
📷 鏡頭管理 (RTSP/狀態監視)
⚙️ 系統設定 (AHP權重/告警門檻)
📊 操作日誌 (誰看了什麼、何時看)
```

***

## 🛡️ 預設帳號

| 角色 | 使用者名稱 | 密碼 | 權限 |
|------|------------|------|------|
| 維安人員 | officer | officer | 車站A儀表板 |
| 場域主管 | supervisor | supervisor | 跨場域查詢 |
| 系統管理員 | admin | admin | 完整後台 |

***

## 📊 系統效能指標

```
即時性: <1s 告警推播 (WebSocket)
併發: 12路 1080p RTSP (30FPS)
準確率: L3/L4預測 >85% (預期)
延遲: 端到端 <500ms
記憶體: 8GB RAM + 1x GPU (RTX 4060)
```

***

## 🔌 API 文件

啟動後訪問：
```
Swagger UI: http://localhost:8000/docs
ReDoc:      http://localhost:8000/redoc
WebSocket:  ws://localhost:8000/ws/alerts
```

主要 API：
```
POST /api/events          # 上報新事件
GET  /api/events          # 事件列表
GET  /api/events/:id      # 事件詳情
GET  /api/events/:id/similar # RAG相似案例
WS   /ws/alerts           # 即時告警推播
```

***

## 🐛 開發指令

```bash
# 前端開發
cd frontend
npm install
npm run dev          # http://localhost:3000

# 後端開發
cd backend
pip install -r requirements.txt
uvicorn main:app --reload  # http://localhost:8000

# 全域開發
docker-compose up -d backend frontend
```

***

## ⚙️ 環境變數

複製 `.env.example` → `.env`：
```bash
DATABASE_URL=postgresql://postgres:password@postgres:5432/attack_intent
REDIS_URL=redis://redis:6379/0
MILVUS_URL=milvus://milvus:19530
JWT_SECRET=your-super-secret-jwt-key-here
```

***

## 📈 部署生產環境

```bash
# 生產部署
docker-compose -f docker-compose.prod.yml up -d

# 監視
docker-compose logs -f backend
docker stats
```

***

## 🤝 貢獻指南

1. Fork 專案
2. 建立功能分支 `git checkout -b feature/xxx`
3. Commit 變更 `git commit -m 'feat: xxx'`
4. Push 分支 `git push origin feature/xxx`
5. 開 Pull Request

***

## 📄 授權

```
MIT License
Copyright (c) 2026 韓佩璇
```

***

**🚀 立即啟動：`docker-compose up -d` → http://localhost:3000** [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71319359/c19902ff-2e91-495b-bea1-a7f7dd704c12/C802-Yan-Jiu-Ji-Hua-Zhai-Yao-Biao-Yun-Yong-Wu-Jian-Zhen-Ce-Yu-Duo-Tong-Dao-Shi-Xu-Fen-Xi-Jin-Xing-Gong-Ji-Yi-Tu-Yu-Ce-Zhi-Yan-Jiu-final.pdf)

<file:1>