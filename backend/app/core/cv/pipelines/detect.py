from pathlib import Path
from typing import Dict, List

from app.core.cv.pipelines.multi_reid import (
    run_detection_multi_reid,
    stop_events,
)

BASE_DIR = Path(__file__).resolve().parents[4]
MODEL_PATH = BASE_DIR / "weights" / "yolo26n.pt"
TRACKER_PATH = BASE_DIR / "app" / "scripts" / "custom_tracker.yaml"
SNAPSHOT_DIR = BASE_DIR / "data" / "snapshots"

CONF_DEFAULT = 0.35
IMG_SIZE = 640

print("========== NEW DETECT.PY LOADED ==========")
print("FILE =", __file__)
print("MODEL_PATH =", MODEL_PATH, MODEL_PATH.exists())
print("TRACKER_PATH =", TRACKER_PATH, TRACKER_PATH.exists())
print("SNAPSHOT_DIR =", SNAPSHOT_DIR)


def open_source(src: str):
    return src


def run_detection(
    source: str = "0",
    conf: float = CONF_DEFAULT,
    save: bool = False,
    task_id: str = "default",
):
    print("\n=== run_detection wrapper start ===")
    print("task_id =", task_id)
    print("source =", source)
    print("conf =", conf)

    run_detection_multi_reid(
        sources=[source],
        conf=conf,
        task_id=task_id,
    )


def run_detection_dual(
    source0: str = "0",
    source1: str = "1",
    conf: float = CONF_DEFAULT,
    task_id: str = "default",
):
    print("\n=== run_detection_dual wrapper start ===")
    print("task_id =", task_id)
    print("source0 =", source0)
    print("source1 =", source1)
    print("conf =", conf)

    run_detection_multi_reid(
        sources=[source0, source1],
        conf=conf,
        task_id=task_id,
    )