# app/core/cv/pipelines/detect.py
import os
import time
from typing import Dict

import cv2
import numpy as np
from ultralytics import YOLO

from app.core.cv.reid import ReIDExtractor, ReIDGallery
from app.core.cv.pipelines.data_recorder import DataRecorder

# =========================
# 路徑與模型設定
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MODEL_PATH = os.path.join(BASE_DIR, "weights", "yolo26n.pt")
TRACKER_PATH = os.path.join(BASE_DIR, "scripts", "custom_tracker.yaml")

CONF_DEFAULT = 0.35
IMG_SIZE = 640

# 全域停止訊號（給 FastAPI router 用）
stop_events: Dict[str, bool] = {}


def open_source(src: str):
    """支援 webcam index 或 rtsp/http 源"""
    try:
        idx = int(src)
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
    except ValueError:
        cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        return None
    return cap


# =========================
# 單鏡頭：帶 Recorder + snapshots
# =========================
def run_detection(source: str = "0", conf: float = 0.5, save: bool = False, task_id: str = "default"):
    """
    單鏡頭 YOLO 偵測（對應 /yolo/start）
    - 持續輸出 snapshots/{task_id}_latest.jpg
    - 同時在 data/sessions/{task_id}/ 寫 frames.jsonl / windows.jsonl / pose/*.npy
    """
    global stop_events
    stop_events[task_id] = False

    if not os.path.exists(MODEL_PATH):
        print(f"❌ 找不到模型檔: {MODEL_PATH}")
        return

    model = YOLO(MODEL_PATH)

    cap = open_source(source)
    if cap is None:
        print(f"❌ 無法開啟來源: {source}")
        stop_events[task_id] = True
        return

    snapshots_dir = os.path.join(BASE_DIR, "data", "snapshots")
    os.makedirs(snapshots_dir, exist_ok=True)
    print(f"[run_detection] 任務 {task_id} 開始執行，來源={source}")

    # ★ Recorder：以 task_id 當 session 名稱
    recorder = DataRecorder(base_dir=BASE_DIR, session_name=task_id)

    prev_time = time.time()
    frame_idx = 0

    try:
        while cap.isOpened():
            if stop_events.get(task_id):
                print(f"[run_detection] 任務 {task_id} 接收到停止指令")
                break

            ret, frame = cap.read()
            if not ret:
                print("[run_detection] 來源讀取失敗，結束")
                break

            results = model.track(
                frame,
                classes=[0],
                conf=conf,
                imgsz=IMG_SIZE,
                persist=True,
                tracker=TRACKER_PATH,  # 你原本用 custom_tracker.yaml 或 botsort.yaml 都可
                verbose=False,
            )

            result = results[0]
            vis = frame.copy()
            ts = time.time()

            if result.boxes is not None and result.boxes.id is not None and len(result.boxes) > 0:
                boxes = result.boxes.xyxy.int().cpu().tolist()
                track_ids = result.boxes.id.int().cpu().tolist()
                confs = result.boxes.conf.cpu().tolist()

                for box, tid, c in zip(boxes, track_ids, confs):
                    x1, y1, x2, y2 = box
                    cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        vis, f"TRACK-{tid} conf:{c:.2f}", (x1, max(20, y1 - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
                    )

                    # 目前先用 track_id 當 person_id，reid_score 暫用 conf 佔位
                    recorder.record_frame(
                        frame_idx=frame_idx,
                        timestamp=ts,
                        camera_id="cam0",
                        person_id=int(tid),
                        track_id=int(tid),
                        bbox=box,
                        reid_score=float(c),
                        landmarks=None,  # 之後接 MediaPipe Pose 再填 33x3
                    )

            # FPS overlay
            now = time.time()
            fps = 1.0 / max(now - prev_time, 1e-6)
            prev_time = now
            cv2.putText(
                vis, f"FPS:{fps:.1f}", (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2
            )

            # Snapshot 給 /yolo/stream 用
            snap_path = os.path.join(snapshots_dir, f"{task_id}_latest.jpg")
            cv2.imwrite(snap_path, vis)

            frame_idx += 1

            # 如果你本地要看畫面，可解開：
            # cv2.imshow(f"task-{task_id}", vis)
            # if cv2.waitKey(1) & 0xFF == ord("q"):
            #     break

        print(f"[run_detection] 任務 {task_id} 結束")

    except Exception as e:
        print(f"⚠️ 偵測過程中發生錯誤: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        stop_events.pop(task_id, None)
        recorder.finalize()
        print(f"[run_detection] 任務 {task_id} 已安全結束")


# =========================
# 雙鏡頭：保留你原本 ReID 邏輯
# （暫時只寫 snapshots，不錄 JSONL；之後要錄再加 Recorder）
# =========================
def run_detection_dual(source0: str, source1: str, conf: float, task_id: str):
    global stop_events
    stop_events[task_id] = False

    model = YOLO(MODEL_PATH)
    reid = ReIDExtractor()
    gallery = ReIDGallery()

    cap0 = open_source(source0)
    cap1 = open_source(source1)
    if cap0 is None or cap1 is None:
        print(f"❌ 雙鏡頭無法開啟來源: {source0} 或 {source1}")
        stop_events[task_id] = True
        return

    snapshot_dir = os.path.join(BASE_DIR, "data", "snapshots")
    os.makedirs(snapshot_dir, exist_ok=True)

    try:
        while cap0.isOpened() and cap1.isOpened():
            if stop_events.get(task_id):
                print(f"[run_detection_dual] 任務 {task_id} 接收到停止指令")
                break

            ret0, frame0 = cap0.read()
            ret1, frame1 = cap1.read()
            if not ret0 or not ret1:
                print("[run_detection_dual] 來源讀取失敗，結束")
                break

            # 兩鏡頭分別 track
            res0 = model.track(
                frame0, classes=[0], conf=conf,
                persist=True, tracker="bytetrack.yaml", verbose=False
            )
            res1 = model.track(
                frame1, classes=[0], conf=conf,
                persist=True, tracker="bytetrack.yaml", verbose=False
            )

            ann0 = apply_reid(frame0, res0[0], "cam0", reid, gallery)
            ann1 = apply_reid(frame1, res1[0], "cam1", reid, gallery)

            cv2.imwrite(os.path.join(snapshot_dir, f"{task_id}_cam0_latest.jpg"), ann0)
            cv2.imwrite(os.path.join(snapshot_dir, f"{task_id}_cam1_latest.jpg"), ann1)

        print(f"[run_detection_dual] 任務 {task_id} 結束")

    finally:
        cap0.release()
        cap1.release()
        stop_events.pop(task_id, None)
        cv2.destroyAllWindows()
        print(f"[run_detection_dual] 任務 {task_id} 已安全結束")


def apply_reid(frame, result, cam_name, reid_extractor: ReIDExtractor, gallery: ReIDGallery):
    vis = frame.copy()
    if result.boxes is None or result.boxes.id is None:
        return vis

    boxes = result.boxes.xyxy.int().cpu().tolist()
    track_ids = result.boxes.id.int().cpu().tolist()

    for box, track_id in zip(boxes, track_ids):
        x1, y1, x2, y2 = box
        crop = frame[y1:y2, x1:x2]
        emb = reid_extractor.extract(crop)
        if emb is None:
            continue

        person_id, note = gallery.resolve(cam_name, track_id, emb)
        color = gallery.get_color(person_id)

        cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            vis, f"P-{person_id} [{note}]",
            (x1, max(20, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2
        )
    return vis