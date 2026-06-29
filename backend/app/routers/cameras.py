from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/cameras", tags=["cameras"])


class CameraItem(BaseModel):
    id: str
    name: str
    source: str


class CameraListResponse(BaseModel):
    count: int
    cameras: list[CameraItem]


@router.get("", response_model=CameraListResponse)
def get_cameras():
    cameras = [
        {"id": "0", "name": "Cam 0", "source": "0"},
        {"id": "1", "name": "Cam 1", "source": "1"},
        {"id": "2", "name": "Cam 2", "source": "2"},
        {"id": "3", "name": "Cam 3", "source": "3"},
    ]

    return {
        "count": len(cameras),
        "cameras": cameras,
    }