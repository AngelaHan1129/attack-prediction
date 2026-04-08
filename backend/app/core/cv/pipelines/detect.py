from pathlib import Path
import time
from typing import Dict, Optional

import cv2
from ultralytics import YOLO

from app.core.cv.pipelines.data_recorder import DataRecorder

BASE_DIR = Path(__file__).resolve().parents[4]
MODEL_PATH = BASE_DIR / "weights" / "yolo26n.pt"
TRACKER_PATH = Path(r"C:\Users\angel\OneDrive - 國立臺中科技大學\桌面\nutc\YS_LAB\研究\attack-prediction\backend\app\scripts\custom_tracker.yaml")
SNAPSHOT_DIR = BASE_DIR / "data" / "snapshots"

CONF_DEFAULT = 0.35
IMG_SIZE = 640

stop_events: Dict[str, bool] = {}

print("========== NEW DETECT.PY LOADED ==========")
print("FILE =", __file__)
print("MODEL_PATH =", MODEL_PATH, MODEL_PATH.exists())
print("TRACKER_PATH =", TRACKER_PATH, TRACKER_PATH.exists())
print("SNAPSHOT_DIR =", SNAPSHOT_DIR)


def open_source(src: str):
    try:
        idx = int(src)
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
    except ValueError:
        cap = cv2.VideoCapture(src)

    if not cap.isOpened():
        return None
    return cap


def run_detection(
    source: str = "0",
    conf: float = CONF_DEFAULT,
    save: bool = False,
    task_id: str = "default",
):
    global stop_events
    stop_events[task_id] = False

    recorder: Optional[DataRecorder] = None
    cap = None

    print("\n=== run_detection start ===")
    print("task_id =", task_id)
    print("source =", source)
    print("MODEL_PATH =", MODEL_PATH, MODEL_PATH.exists())
    print("TRACKER_PATH =", TRACKER_PATH, TRACKER_PATH.exists())
    print("SNAPSHOT_DIR =", SNAPSHOT_DIR)

    if not MODEL_PATH.exists():
        print(f"❌ 找不到模型檔: {MODEL_PATH}")
        stop_events.pop(task_id, None)
        return

    if not TRACKER_PATH.exists():
        print(f"❌ 找不到 tracker 設定: {TRACKER_PATH}")
        stop_events.pop(task_id, None)
        return

    try:
        model = YOLO(str(MODEL_PATH))
        print("✅ YOLO model loaded")
    except Exception as e:
        print(f"❌ YOLO model 載入失敗: {e}")
        stop_events.pop(task_id, None)
        return

    cap = open_source(source)
    if cap is None:
        print(f"❌ 無法開啟來源: {source}")
        stop_events.pop(task_id, None)
        return

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✅ snapshot dir ready: {SNAPSHOT_DIR}")

    try:
        recorder = DataRecorder(base_dir=str(BASE_DIR), session_name=task_id)
        print("✅ DataRecorder initialized")
    except Exception as e:
        print(f"❌ DataRecorder 初始化失敗: {e}")
        cap.release()
        stop_events.pop(task_id, None)
        return

    prev_time = time.time()
    frame_idx = 0

    try:
        while cap.isOpened():
            if stop_events.get(task_id):
                print(f"[run_detection] 任務 {task_id} 接收到停止指令")
                break

            ret, frame = cap.read()
            print(f"[run_detection] cap.read() -> ret={ret}")

            if not ret:
                print("[run_detection] 來源讀取失敗，結束")
                break

            results = model.track(
                frame,
                classes=[0],
                conf=conf,
                imgsz=IMG_SIZE,
                persist=True,
                tracker=str(TRACKER_PATH),
                verbose=False,
            )
            print("[run_detection] model.track() ok")

            result = results[0]
            vis = frame.copy()
            ts = time.time()

            if result.boxes is not None and result.boxes.id is not None and len(result.boxes) > 0:
                boxes = result.boxes.xyxy.int().cpu().tolist()
                track_ids = result.boxes.id.int().cpu().tolist()
                confs = result.boxes.conf.cpu().tolist()
                print(f"[run_detection] tracked persons = {len(boxes)}")

                for box, tid, c in zip(boxes, track_ids, confs):
                    x1, y1, x2, y2 = box

                    cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        vis,
                        f"TRACK-{tid} conf:{c:.2f}",
                        (x1, max(20, y1 - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )

                    recorder.record_frame(
                        frame_idx=frame_idx,
                        timestamp=ts,
                        camera_id="cam0",
                        person_id=int(tid),
                        track_id=int(tid),
                        bbox=box,
                        reid_score=float(c),
                        landmarks=None,
                    )
            else:
                print("[run_detection] no tracked person, still saving frame")

            now = time.time()
            fps = 1.0 / max(now - prev_time, 1e-6)
            prev_time = now

            cv2.putText(
                vis,
                f"FPS:{fps:.1f}",
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 0),
                2,
            )

            snap_path = SNAPSHOT_DIR / f"{task_id}_latest.jpg"
            ok = cv2.imwrite(str(snap_path), vis)
            print(f"[run_detection] write snapshot -> {snap_path}, ok={ok}")

            frame_idx += 1

        print(f"[run_detection] 任務 {task_id} 結束")

    except Exception as e:
        print(f"⚠️ 偵測過程中發生錯誤: {repr(e)}")
    finally:
        if cap is not None:
            cap.release()

        cv2.destroyAllWindows()
        stop_events.pop(task_id, None)

        if recorder is not None:
            try:
                recorder.finalize()
            except Exception as e:
                print(f"⚠️ recorder.finalize() 失敗: {e}")

        print(f"[run_detection] 任務 {task_id} 已安全結束")
        
def run_detection_dual(
    source0: str = "0",
    source1: str = "1",
    conf: float = 0.5,
    task_id: str = "default",
):
    global stop_events
    stop_events[task_id] = False

    cap0 = None
    cap1 = None

    print("\n=== run_detection_dual start ===")
    print("task_id =", task_id)
    print("source0 =", source0)
    print("source1 =", source1)
    print("MODEL_PATH =", MODEL_PATH, MODEL_PATH.exists())
    print("TRACKER_PATH =", TRACKER_PATH, TRACKER_PATH.exists())
    print("SNAPSHOT_DIR =", SNAPSHOT_DIR)

    if not MODEL_PATH.exists():
        print(f"❌ 找不到模型檔: {MODEL_PATH}")
        stop_events.pop(task_id, None)
        return

    if not TRACKER_PATH.exists():
        print(f"❌ 找不到 tracker 設定: {TRACKER_PATH}")
        stop_events.pop(task_id, None)
        return

    try:
        model = YOLO(str(MODEL_PATH))
        print("✅ YOLO model loaded (dual)")
    except Exception as e:
        print(f"❌ YOLO model 載入失敗 (dual): {e}")
        stop_events.pop(task_id, None)
        return

    cap0 = open_source(source0)
    cap1 = open_source(source1)

    if cap0 is None or cap1 is None:
        print(f"❌ 無法開啟雙鏡頭來源: source0={source0}, source1={source1}")
        if cap0 is not None:
            cap0.release()
        if cap1 is not None:
            cap1.release()
        stop_events.pop(task_id, None)
        return

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✅ snapshot dir ready (dual): {SNAPSHOT_DIR}")

    try:
        while cap0.isOpened() and cap1.isOpened():
            if stop_events.get(task_id):
                print(f"[run_detection_dual] 任務 {task_id} 接收到停止指令")
                break

            ret0, frame0 = cap0.read()
            ret1, frame1 = cap1.read()
            print(f"[run_detection_dual] cap.read() -> ret0={ret0}, ret1={ret1}")

            if not ret0 or not ret1:
                print("[run_detection_dual] 來源讀取失敗，結束")
                break

            res0 = model.track(
                frame0,
                classes=[0],
                conf=conf,
                imgsz=IMG_SIZE,
                persist=True,
                tracker=str(TRACKER_PATH),
                verbose=False,
            )
            res1 = model.track(
                frame1,
                classes=[0],
                conf=conf,
                imgsz=IMG_SIZE,
                persist=True,
                tracker=str(TRACKER_PATH),
                verbose=False,
            )

            vis0 = res0[0].plot()
            vis1 = res1[0].plot()

            snap0 = SNAPSHOT_DIR / f"{task_id}_cam0_latest.jpg"
            snap1 = SNAPSHOT_DIR / f"{task_id}_cam1_latest.jpg"

            ok0 = cv2.imwrite(str(snap0), vis0)
            ok1 = cv2.imwrite(str(snap1), vis1)

            print(f"[run_detection_dual] write cam0 -> {snap0}, ok={ok0}")
            print(f"[run_detection_dual] write cam1 -> {snap1}, ok={ok1}")

        print(f"[run_detection_dual] 任務 {task_id} 結束")

    except Exception as e:
        print(f"⚠️ 雙鏡頭偵測過程中發生錯誤: {repr(e)}")
    finally:
        if cap0 is not None:
            cap0.release()
        if cap1 is not None:
            cap1.release()

        cv2.destroyAllWindows()
        stop_events.pop(task_id, None)
        print(f"[run_detection_dual] 任務 {task_id} 已安全結束")