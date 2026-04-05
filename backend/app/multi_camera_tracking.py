from ultralytics import YOLO
import cv2
import numpy as np
import time
from collections import defaultdict
import os

# =========================
# 路徑設定
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
MODEL_PATH = os.path.join(BASE_DIR, "weights", "yolo26n.pt")
TRACKER_PATH = os.path.join(BASE_DIR, "scripts", "custom_tracker.yaml")

# =========================
# 攝影機設定
# =========================
CAMERA_0 = 0
CAMERA_1 = 1
CAM_BACKEND = cv2.CAP_DSHOW

# =========================
# YOLO / Tracking 參數
# =========================
CONF = 0.35
IMG_SIZE = 640
MAX_TRACK_HISTORY = 30

# 每台鏡頭各自維護軌跡歷史
track_history_cam0 = defaultdict(list)
track_history_cam1 = defaultdict(list)


# =========================
# 工具函式
# =========================
def open_camera(index):
    cap = cv2.VideoCapture(index, CAM_BACKEND)
    if not cap.isOpened():
        return None
    return cap


def draw_tracks(vis, boxes, track_ids, confs, track_history, camera_name):
    """
    把追蹤框、track_id、軌跡畫到畫面上
    """
    for box, track_id, conf in zip(boxes, track_ids, confs):
        x1, y1, x2, y2 = box

        # 1. 畫框
        color = (0, 255, 0)
        cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)

        # 2. 顯示文字
        label_1 = f"{camera_name} TRACK-{track_id}"
        label_2 = f"conf:{conf:.2f}"
        cv2.putText(
            vis, label_1, (x1, max(20, y1 - 28)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2
        )
        cv2.putText(
            vis, label_2, (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2
        )

        # 3. 更新軌跡歷史
        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)
        track_history[track_id].append((cx, cy))

        if len(track_history[track_id]) > MAX_TRACK_HISTORY:
            track_history[track_id].pop(0)

        # 4. 畫軌跡線
        if len(track_history[track_id]) >= 2:
            points = np.array(track_history[track_id], dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(vis, [points], False, (200, 200, 200), 2)

        # 5. 畫中心點
        cv2.circle(vis, (cx, cy), 4, (0, 255, 255), -1)


def process_camera_frame(model, frame, camera_name, track_history):
    """
    對單一鏡頭畫面做 YOLO + ByteTrack
    """
    results = model.track(
        frame,
        classes=[0],                  # 只追蹤 person
        conf=CONF,
        imgsz=IMG_SIZE,
        persist=True,                 # 關鍵：保留前一幀追蹤狀態
        tracker=TRACKER_PATH,         # 使用自訂 ByteTrack 設定
        verbose=False
    )

    result = results[0]
    vis = frame.copy()

    # 若當前幀沒有追到任何有效 ID
    if result.boxes is None or result.boxes.id is None or len(result.boxes) == 0:
        cv2.putText(
            vis, f"{camera_name}: no tracked person",
            (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 180, 255), 2
        )
        return vis

    boxes = result.boxes.xyxy.int().cpu().tolist()
    track_ids = result.boxes.id.int().cpu().tolist()
    confs = result.boxes.conf.cpu().tolist()

    draw_tracks(vis, boxes, track_ids, confs, track_history, camera_name)
    return vis


def main():
    # 1. 載入模型
    model = YOLO(MODEL_PATH)

    # 2. 開啟鏡頭
    cap1 = open_camera(CAMERA_0)
    cap2 = open_camera(CAMERA_1)

    if cap1 is None:
        print("鏡頭 0 無法開啟")
        return

    if cap2 is None:
        print("鏡頭 1 無法開啟")
        cap1.release()
        return

    prev_time = time.time()

    while True:
        ret1, frame1 = cap1.read()
        ret2, frame2 = cap2.read()

        if not ret1 or not ret2:
            print("其中一台鏡頭讀取失敗")
            break

        # 3. 各自處理每台鏡頭
        out1 = process_camera_frame(model, frame1, "cam0", track_history_cam0)
        out2 = process_camera_frame(model, frame2, "cam1", track_history_cam1)

        # 4. FPS 顯示
        now = time.time()
        fps = 1.0 / max(now - prev_time, 1e-6)
        prev_time = now

        cv2.putText(
            out1, f"cam0 FPS:{fps:.1f}", (20, 60),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2
        )
        cv2.putText(
            out2, f"cam1 FPS:{fps:.1f}", (20, 60),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2
        )

        # 5. 拼接雙鏡畫面
        combined = np.hstack([
            cv2.resize(out1, (640, 480)),
            cv2.resize(out2, (640, 480))
        ])

        cv2.imshow("YOLO + ByteTrack Stable Tracking", combined)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    cap1.release()
    cap2.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()