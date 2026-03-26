from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os

# 引用你之前在 core/cv/pipelines 寫好的偵測邏輯
# 假設你的 detect.py 裡面有一個偵測 Class 或 Function
from app.core.cv.pipelines.detect import run_detection 

router = APIRouter()

# 定義請求格式
class DetectionRequest(BaseModel):
    source: str = "0"  # 預設為第一個攝影機，也可以是影片路徑
    save_video: bool = True
    conf_threshold: float = 0.25

# 定義回應格式
class DetectionResponse(BaseModel):
    task_id: str
    status: str
    message: str

# 模擬一個簡單的任務追蹤（實際開發建議用 Redis 或資料庫）
active_tasks = {}

@router.post("/start", response_model=DetectionResponse)
async def start_detection(request: DetectionRequest, background_tasks: BackgroundTasks):
    """
    啟動 YOLO 偵測任務（後台執行）
    """
    task_id = f"task_{len(active_tasks) + 1}"
    
    if task_id in active_tasks and active_tasks[task_id] == "running":
        raise HTTPException(status_code=400, detail="Task is already running")

    # 將耗時的偵測邏輯丟到後台執行
    background_tasks.add_task(
        run_detection, 
        source=request.source, 
        conf=request.conf_threshold,
        save=request.save_video,
        task_id=task_id
    )
    
    active_tasks[task_id] = "running"
    
    return {
        "task_id": task_id,
        "status": "started",
        "message": f"偵測任務已在後台啟動，來源：{request.source}"
    }

@router.get("/status/{task_id}")
async def get_status(task_id: str):
    """
    查詢特定偵測任務的狀態
    """
    status = active_tasks.get(task_id, "not_found")
    return {"task_id": task_id, "status": status}

@router.get("/latest-snapshots")
async def list_snapshots():
    """
    列出最新的偵測截圖（對應你 data/snapshots 目錄）
    """
    snapshot_path = "data/snapshots"
    if not os.path.exists(snapshot_path):
        return {"files": []}
    
    files = os.listdir(snapshot_path)
    return {"files": sorted(files, reverse=True)}