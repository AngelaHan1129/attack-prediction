import os
import uuid
from typing import Dict
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from app.core.dependencies import require_admin
from app.core.cv.pipelines.detect import run_detection, run_detection_dual, stop_events

router = APIRouter(prefix="/yolo", tags=["YOLO Analysis"])

active_tasks: Dict[str, str] = {}
SECURITY_SCHEMA = [{"bearer": []}]


@router.post("/start", response_model=dict, openapi_extra={"security": SECURITY_SCHEMA})
async def start_yolo(
    background_tasks: BackgroundTasks,
    source: str = "0",
    current_user=Depends(require_admin)
):
    """🚀 啟動單鏡頭 YOLO 偵測任務 (僅限管理員)"""
    running_tasks = [tid for tid, s in active_tasks.items() if s == "running"]
    if running_tasks:
        return {"status": "error", "message": "目前已有任務正在執行中",
                "active_task_id": running_tasks[0]}

    task_id = str(uuid.uuid4())[:8]
    active_tasks[task_id] = "running"
    stop_events[task_id] = False

    background_tasks.add_task(run_detection, source=source, conf=0.5, task_id=task_id)

    return {"status": "success", "message": "YOLO 偵測任務已啟動",
            "task_id": task_id, "source": source, "started_by": current_user.email}


@router.post("/start/dual", response_model=dict, openapi_extra={"security": SECURITY_SCHEMA})
async def start_yolo_dual(
    background_tasks: BackgroundTasks,
    source0: str = "0",
    source1: str = "1",
    current_user=Depends(require_admin)
):
    """🚀 啟動雙鏡頭 YOLO 偵測任務 (僅限管理員)"""
    running_tasks = [tid for tid, s in active_tasks.items() if s == "running"]
    if running_tasks:
        return {"status": "error", "message": "目前已有任務在執行中",
                "active_task_id": running_tasks[0]}

    task_id = str(uuid.uuid4())[:8]
    active_tasks[task_id] = "running"
    stop_events[task_id] = False

    background_tasks.add_task(run_detection_dual, source0=source0,
                               source1=source1, conf=0.5, task_id=task_id)

    return {"status": "success", "message": "雙鏡頭偵測任務已啟動",
            "task_id": task_id, "source0": source0, "source1": source1,
            "started_by": current_user.email}


@router.get("/status/{task_id}", openapi_extra={"security": SECURITY_SCHEMA})
async def get_task_status(task_id: str, current_user=Depends(require_admin)):
    """🔍 查詢任務狀態"""
    status = active_tasks.get(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="找不到該任務 ID")

    if task_id not in stop_events and status == "running":
        active_tasks[task_id] = "finished"
        status = "finished"

    return {"task_id": task_id, "status": status}


@router.post("/stop/{task_id}", openapi_extra={"security": SECURITY_SCHEMA})
async def stop_yolo(task_id: str, current_user=Depends(require_admin)):
    """🛑 強制停止偵測任務"""
    if task_id in active_tasks:
        stop_events[task_id] = True
        active_tasks[task_id] = "stopped"
        return {"status": "success", "message": f"任務 {task_id} 已發送停止指令"}

    raise HTTPException(status_code=404, detail="任務不存在或已結束")


# ✅ 改名為 get_frame_single，避免與雙鏡頭衝突
@router.get("/stream/{task_id}")
async def get_frame_single(task_id: str):
    """🖼️ 單鏡頭截圖"""
    img_path = os.path.join("data", "snapshots", f"{task_id}_latest.jpg")

    if os.path.exists(img_path):
        return FileResponse(img_path, media_type="image/jpeg",
                            headers={"Cache-Control": "no-cache"})

    raise HTTPException(status_code=404, detail="尚未產生影像畫面或任務已失效")


# ✅ 雙鏡頭用 cam0 / cam1 區分
@router.get("/stream/{task_id}/{cam}")
async def get_frame_dual(task_id: str, cam: str = "cam0"):
    """🖼️ 雙鏡頭截圖，cam 傳 cam0 或 cam1"""
    img_path = os.path.join("data", "snapshots", f"{task_id}_{cam}_latest.jpg")

    if not os.path.exists(img_path):
        img_path = os.path.join("data", "snapshots", f"{task_id}_latest.jpg")

    if os.path.exists(img_path):
        return FileResponse(img_path, media_type="image/jpeg",
                            headers={"Cache-Control": "no-cache"})

    raise HTTPException(status_code=404, detail="尚未產生影像畫面")


@router.get("/tasks", openapi_extra={"security": SECURITY_SCHEMA})
async def list_all_tasks(current_user=Depends(require_admin)):
    """📋 列出所有任務"""
    return {"tasks": active_tasks}