from fastapi import APIRouter, Depends, UploadFile
from app.core.dependencies import require_admin
from services import detect  # 你的 detect.py

router = APIRouter(prefix="/yolo", tags=["YOLO"])

@router.post("/detect")
async def yolo_detect(file: UploadFile = None, current_user=Depends(require_admin)):
    # 整合你的 detect.py
    result = detect.run(model_path="services/models/yolo26n.pt", source=file.filename)
    return {"detections": result}

@router.get("/camera")
async def camera_stream(current_user=Depends(require_admin)):
    # 呼叫 camera.py
    return {"stream": "rtsp://your-stream"}
