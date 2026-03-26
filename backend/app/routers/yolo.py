import os
import uuid
from typing import Dict
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, UploadFile
from fastapi.responses import FileResponse

# 核心邏輯與權限引用
from app.core.dependencies import require_admin
from app.core.cv.pipelines.detect import run_detection, stop_events

router = APIRouter(prefix="/yolo", tags=["YOLO Analysis"])

# 用於追蹤記憶體中的任務狀態 (key: task_id, value: status_string)
# 實務上若需重啟後維持，建議存入資料庫
active_tasks: Dict[str, str] = {}

# --- 配置 Swagger 鎖頭定義 ---
SECURITY_SCHEMA = [{"bearer": []}]

@router.post(
    "/start", 
    response_model=dict,
    openapi_extra={"security": SECURITY_SCHEMA}
)
async def start_yolo(
    background_tasks: BackgroundTasks,
    source: str = "0",  # 0 為預設相機，也可傳入影片路徑或串流位址
    current_user=Depends(require_admin)
):
    """
    🚀 啟動 YOLO 偵測任務 (僅限管理員)
    """
    # 1. 檢查是否有正在執行的任務，避免資源耗盡
    running_tasks = [tid for tid, status in active_tasks.items() if status == "running"]
    if running_tasks:
        return {
            "status": "error",
            "message": "目前已有任務正在執行中",
            "active_task_id": running_tasks[0]
        }

    # 2. 產生唯一任務 ID
    task_id = str(uuid.uuid4())[:8]
    active_tasks[task_id] = "running"
    
    # 3. 確保停止訊號初始為 False
    stop_events[task_id] = False

    # 4. 派發背景任務 (不會阻塞 API 回傳)
    background_tasks.add_task(
        run_detection, 
        source=source, 
        conf=0.5, 
        task_id=task_id
    )

    return {
        "status": "success",
        "message": "YOLO 偵測任務已啟動",
        "task_id": task_id,
        "source": source,
        "started_by": current_user.email
    }

@router.get(
    "/status/{task_id}", 
    openapi_extra={"security": SECURITY_SCHEMA}
)
async def get_task_status(task_id: str, current_user=Depends(require_admin)):
    """
    🔍 查詢特定任務目前的執行狀態
    """
    status = active_tasks.get(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="找不到該任務 ID")
    
    # 檢查 detect.py 是否已經自動結束
    if task_id not in stop_events and status == "running":
        active_tasks[task_id] = "finished"
        status = "finished"

    return {"task_id": task_id, "status": status}

@router.post(
    "/stop/{task_id}", 
    openapi_extra={"security": SECURITY_SCHEMA}
)
async def stop_yolo(task_id: str, current_user=Depends(require_admin)):
    """
    🛑 強制停止指定的偵測任務
    """
    if task_id in active_tasks:
        # 設定停止 Flag，detect.py 的 while 迴圈會偵測到並跳出
        stop_events[task_id] = True
        active_tasks[task_id] = "stopped"
        return {"status": "success", "message": f"任務 {task_id} 已發送停止指令"}
    
    raise HTTPException(status_code=404, detail="任務不存在或已結束")

@router.get("/stream/{task_id}")
async def get_latest_frame(task_id: str):
    """
    🖼️ 獲取最新的偵測截圖 (供前端 React <img> 每秒更新)
    注意：此路徑不設權限檢查，方便前端 <img> 標籤直接引用
    """
    # 對應 detect.py 中 cv2.imwrite 的路徑
    img_path = os.path.join("data", "snapshots", f"{task_id}_latest.jpg")
    
    if os.path.exists(img_path):
        # 使用 FileResponse 回傳影像，並停用快取
        return FileResponse(
            img_path, 
            media_type="image/jpeg",
            headers={"Cache-Control": "no-cache"}
        )
    
    raise HTTPException(status_code=404, detail="尚未產生影像畫面或任務已失效")

@router.get("/tasks", openapi_extra={"security": SECURITY_SCHEMA})
async def list_all_tasks(current_user=Depends(require_admin)):
    """
    📋 列出歷史與目前的任務清單
    """
    return {"tasks": active_tasks}