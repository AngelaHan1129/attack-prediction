import uuid
from pathlib import Path
from typing import Dict, List

import cv2
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.core.dependencies import require_admin
from app.core.cv.pipelines.detect import run_detection, stop_events
from app.core.cv.pipelines.dual_reid import run_detection_dual_reid
from app.core.cv.pipelines.multi_reid import run_detection_multi_reid

router = APIRouter(prefix="/yolo", tags=["YOLO Analysis"])

active_tasks: Dict[str, str] = {}
SECURITY_SCHEMA = [{"bearer": []}]

BASE_DIR = Path(__file__).resolve().parents[2]
SNAPSHOT_DIR = BASE_DIR / "data" / "snapshots"


class CameraItem(BaseModel):
    id: str
    name: str
    source: str
    streamUrl: str | None = None


class CameraListResponse(BaseModel):
    count: int
    cameras: List[CameraItem]


def ensure_no_running_task():
    running_tasks = [tid for tid, s in active_tasks.items() if s == "running"]
    if running_tasks:
        return running_tasks[0]
    return None


def parse_sources_csv(sources: str) -> List[str]:
    values = [s.strip() for s in sources.split(",") if s.strip()]
    if not values:
        raise HTTPException(status_code=400, detail="sources 不可為空")
    return values


def image_no_cache_headers():
    return {
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
    }


def read_image_response(img_path: Path) -> Response:
    img = cv2.imread(str(img_path))
    if img is None:
        raise HTTPException(status_code=503, detail="Frame decode failed")

    ok, buf = cv2.imencode(".jpg", img)
    if not ok:
        raise HTTPException(status_code=503, detail="Frame encode failed")

    return Response(
        content=buf.tobytes(),
        media_type="image/jpeg",
        headers=image_no_cache_headers(),
    )


@router.get("/cameras", response_model=CameraListResponse)
async def get_cameras():
    cameras = []
    found_sources = set()

    backends = [
        ("DSHOW", cv2.CAP_DSHOW),
        ("MSMF", cv2.CAP_MSMF),
    ]

    for i in range(0, 20):
        for backend_name, backend in backends:
            cap = None
            try:
                cap = cv2.VideoCapture(i, backend)
                if not cap.isOpened():
                    continue

                ok, _ = cap.read()
                if ok and str(i) not in found_sources:
                    cameras.append(
                        {
                            "id": f"cam{i}",
                            "name": f"Camera {i}",
                            "source": str(i),
                            "streamUrl": None,
                        }
                    )
                    found_sources.add(str(i))
                    print(f"[camera-detected] index={i}, backend={backend_name}")
                    break
            finally:
                if cap is not None:
                    cap.release()

    cameras = cameras[:3]

    return {
        "count": len(cameras),
        "cameras": cameras,
    }
    

    cameras = []
    found_sources = set()

    backends = [
        ("DSHOW", cv2.CAP_DSHOW),
        ("MSMF", cv2.CAP_MSMF),
    ]

    for i in range(0, 20):
        detected = False

        for backend_name, backend in backends:
            cap = None
            try:
                cap = cv2.VideoCapture(i, backend)
                opened = cap.isOpened()
                print(f"[camera-scan] index={i}, backend={backend_name}, opened={opened}")

                if not opened:
                    continue

                ok, _ = cap.read()
                print(f"[camera-scan] index={i}, backend={backend_name}, read_ok={ok}")

                if ok and str(i) not in found_sources:
                    cameras.append(
                        {
                            "id": f"cam{i}",
                            "name": f"Camera {i}",
                            "source": str(i),
                            "streamUrl": None,
                        }
                    )
                    found_sources.add(str(i))
                    detected = True
                    break

            except Exception as e:
                print(f"[camera-scan] index={i}, backend={backend_name}, error={e}")

            finally:
                if cap is not None:
                    cap.release()

        if not detected:
            print(f"[camera-scan] index={i} not available")

    return {
        "count": len(cameras),
        "cameras": cameras,
    }

    cameras = []

    for i in range(0, 10):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)  # Windows 建議先試 DSHOW
        if cap is not None and cap.isOpened():
            ok, _ = cap.read()
            if ok:
                cameras.append(
                    {
                        "id": f"cam{i}",
                        "name": f"Camera {i}",
                        "source": str(i),
                        "streamUrl": None,
                    }
                )
        if cap is not None:
            cap.release()

    return {
        "count": len(cameras),
        "cameras": cameras,
    }

@router.post("/start", response_model=dict, openapi_extra={"security": SECURITY_SCHEMA})
async def start_yolo(
    background_tasks: BackgroundTasks,
    source: str = "0",
    current_user=Depends(require_admin)
):
    running_task_id = ensure_no_running_task()
    if running_task_id:
        return {
            "status": "error",
            "message": "已有 YOLO 任務正在執行",
            "active_task_id": running_task_id
        }

    task_id = str(uuid.uuid4())[:8]
    active_tasks[task_id] = "running"
    stop_events[task_id] = False

    background_tasks.add_task(
        run_detection,
        source=source,
        conf=0.5,
        task_id=task_id
    )

    return {
        "status": "success",
        "message": "YOLO 單鏡頭統一 ReID 任務已啟動",
        "task_id": task_id,
        "source": source,
        "started_by": current_user.email
    }


@router.post("/start/dual", response_model=dict, openapi_extra={"security": SECURITY_SCHEMA})
async def start_yolo_dual(
    background_tasks: BackgroundTasks,
    source0: str = "0",
    source1: str = "1",
    current_user=Depends(require_admin)
):
    running_task_id = ensure_no_running_task()
    if running_task_id:
        return {
            "status": "error",
            "message": "已有 YOLO 任務正在執行",
            "active_task_id": running_task_id
        }

    task_id = str(uuid.uuid4())[:8]
    active_tasks[task_id] = "running"
    stop_events[task_id] = False

    background_tasks.add_task(
        run_detection_dual_reid,
        source0=source0,
        source1=source1,
        conf=0.5,
        task_id=task_id
    )

    return {
        "status": "success",
        "message": "YOLO 雙鏡頭統一 ReID 任務已啟動",
        "task_id": task_id,
        "source0": source0,
        "source1": source1,
        "started_by": current_user.email
    }


@router.post("/start/multi", response_model=dict, openapi_extra={"security": SECURITY_SCHEMA})
async def start_yolo_multi(
    background_tasks: BackgroundTasks,
    sources: str = "0,1",
    current_user=Depends(require_admin)
):
    running_task_id = ensure_no_running_task()
    if running_task_id:
        return {
            "status": "error",
            "message": "已有 YOLO 任務正在執行",
            "active_task_id": running_task_id
        }

    source_list = parse_sources_csv(sources)

    task_id = str(uuid.uuid4())[:8]
    active_tasks[task_id] = "running"
    stop_events[task_id] = False

    background_tasks.add_task(
        run_detection_multi_reid,
        sources=source_list,
        conf=0.5,
        task_id=task_id
    )

    return {
        "status": "success",
        "message": "YOLO 多鏡頭統一 ReID 任務已啟動",
        "task_id": task_id,
        "sources": source_list,
        "started_by": current_user.email
    }


@router.get("/status/{task_id}", openapi_extra={"security": SECURITY_SCHEMA})
async def get_task_status(task_id: str, current_user=Depends(require_admin)):
    status = active_tasks.get(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="找不到 task ID")

    if task_id not in stop_events and status == "running":
        active_tasks[task_id] = "finished"
        status = "finished"

    return {
        "task_id": task_id,
        "status": status
    }


@router.post("/stop/{task_id}", openapi_extra={"security": SECURITY_SCHEMA})
async def stop_yolo(task_id: str, current_user=Depends(require_admin)):
    if task_id in active_tasks:
        stop_events[task_id] = True
        active_tasks[task_id] = "stopped"
        return {
            "status": "success",
            "message": f"任務 {task_id} 已停止"
        }

    raise HTTPException(status_code=404, detail="找不到 task ID")


@router.get("/stream/{task_id}/{cam}")
async def get_frame_by_cam(task_id: str, cam: str):
    img_path = SNAPSHOT_DIR / f"{task_id}_{cam}_latest.jpg"
    print(f"[get_frame_by_cam] checking: {img_path} exists={img_path.exists()}")

    if not img_path.exists():
        raise HTTPException(status_code=404, detail=f"Frame not ready: {img_path}")

    return read_image_response(img_path)


@router.get("/stream/{task_id}")
async def get_frame_single(task_id: str):
    preferred = SNAPSHOT_DIR / f"{task_id}_cam0_latest.jpg"
    legacy = SNAPSHOT_DIR / f"{task_id}_latest.jpg"

    print(f"[get_frame_single] checking preferred={preferred.exists()} legacy={legacy.exists()}")

    img_path = preferred if preferred.exists() else legacy if legacy.exists() else None

    if img_path is None:
        raise HTTPException(status_code=404, detail=f"Frame not ready for task {task_id}")

    return read_image_response(img_path)


@router.get("/tasks", openapi_extra={"security": SECURITY_SCHEMA})
async def list_all_tasks(current_user=Depends(require_admin)):
    return {"tasks": active_tasks}