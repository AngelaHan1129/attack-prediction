import cv2
import os
import time
from ultralytics import YOLO
from app.core.cv.reid import ReIDExtractor, ReIDGallery

# 全域停止訊號
stop_events = {}


def run_detection(source="0", conf=0.5, save=False, task_id="default"):
    global stop_events
    stop_events[task_id] = False

    model_path = os.path.join("weights", "yolo26n.pt")
    if not os.path.exists(model_path):
        print(f"❌ 找不到模型檔: {model_path}")
        return

    model = YOLO(model_path)

    src = int(source) if str(source).isdigit() else source
    cap = cv2.VideoCapture(src, cv2.CAP_DSHOW) if isinstance(src, int) else cv2.VideoCapture(src)

    if not cap.isOpened():
        print(f"❌ 無法開啟來源: {src}")
        return

    snapshot_dir = os.path.join("data", "snapshots")
    os.makedirs(snapshot_dir, exist_ok=True)
    print(f"任務 {task_id} 開始執行...")

    try:
        while cap.isOpened():
            if stop_events.get(task_id):
                print(f"任務 {task_id} 接收到停止指令")
                break

            ret, frame = cap.read()
            if not ret:
                break

            results = model.track(
                frame,
                classes=[0],
                conf=conf,
                persist=True,
                tracker="botsort.yaml",
                verbose=False
            )

            if results[0].boxes is not None and results[0].boxes.id is not None:
                annotated_frame = results[0].plot()
                cv2.imwrite(os.path.join(snapshot_dir, f"{task_id}_latest.jpg"), annotated_frame)
            else:
                cv2.imwrite(os.path.join(snapshot_dir, f"{task_id}_latest.jpg"), frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        print(f"⚠️ 偵測過程中發生錯誤: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        stop_events.pop(task_id, None)
        print(f"任務 {task_id} 已安全結束")


def run_detection_dual(source0: str, source1: str, conf: float, task_id: str):
    stop_events[task_id] = False

    model = YOLO(os.path.join("weights", "yolo26n.pt"))
    reid  = ReIDExtractor()
    gallery = ReIDGallery()  # 跨鏡頭全域 person_db

    cap0 = cv2.VideoCapture(int(source0) if source0.isdigit() else source0)
    cap1 = cv2.VideoCapture(int(source1) if source1.isdigit() else source1)

    snapshot_dir = os.path.join("data", "snapshots")
    os.makedirs(snapshot_dir, exist_ok=True)

    try:
        while cap0.isOpened() and cap1.isOpened():
            if stop_events.get(task_id):
                break

            ret0, frame0 = cap0.read()
            ret1, frame1 = cap1.read()
            if not ret0 or not ret1:
                break

            # 兩鏡頭分別 track（各自 persist）
            res0 = model.track(frame0, classes=[0], conf=conf,
                               persist=True, tracker="bytetrack.yaml", verbose=False)
            res1 = model.track(frame1, classes=[0], conf=conf,
                               persist=True, tracker="bytetrack.yaml", verbose=False)

            ann0 = apply_reid(frame0, res0[0], "cam0", reid, gallery)
            ann1 = apply_reid(frame1, res1[0], "cam1", reid, gallery)

            cv2.imwrite(f"{snapshot_dir}/{task_id}_cam0_latest.jpg", ann0)
            cv2.imwrite(f"{snapshot_dir}/{task_id}_cam1_latest.jpg", ann1)

    finally:
        cap0.release()
        cap1.release()
        stop_events.pop(task_id, None)


def apply_reid(frame, result, cam_name, reid_extractor, gallery):
    vis = frame.copy()
    if result.boxes is None or result.boxes.id is None:
        return vis

    boxes     = result.boxes.xyxy.int().cpu().tolist()
    track_ids = result.boxes.id.int().cpu().tolist()

    for box, track_id in zip(boxes, track_ids):
        x1, y1, x2, y2 = box
        crop = frame[y1:y2, x1:x2]
        emb  = reid_extractor.extract(crop)
        if emb is None:
            continue

        person_id, note = gallery.resolve(cam_name, track_id, emb)

        color = gallery.get_color(person_id)
        cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)
        cv2.putText(vis, f"P-{person_id} [{note}]",
                    (x1, max(20, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
    return vis
