import time
import threading
from pathlib import Path
from collections import deque
from typing import Dict, List, Optional, Tuple, Any

import cv2
import numpy as np
import torch
import torchvision.transforms as T
import mediapipe as mp
import torchreid

from ultralytics import YOLO

from app.core.cv.pipelines.data_recorder import DataRecorder


BASE_DIR = Path(__file__).resolve().parents[4]
SNAPSHOT_DIR = BASE_DIR / "data" / "snapshots"
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = BASE_DIR / "weights" / "yolo26n.pt"
POSE_TASK_PATH = BASE_DIR / "weights" / "pose_landmarker_lite.task"
TRACKER_PATH = BASE_DIR / "app" / "scripts" / "custom_tracker.yaml"

CONF_DEFAULT = 0.45
IMG_SIZE = 640
MAX_GALLERY_PER_PERSON = 12
MAX_SKELETON_SEQ = 150
REID_MATCH_THRESHOLD = 0.72
REID_STRONG_THRESHOLD = 0.82
TRACK_CACHE_MAX_IDLE_SEC = 2.5
PERSON_DB_MAX_IDLE_SEC = 60.0
MIN_CROP_H = 120
MIN_CROP_W = 60
MIN_SHARPNESS = 35.0

stop_events: Dict[str, bool] = {}

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

reid_model = torchreid.models.build_model(
    name="osnet_x1_0",
    num_classes=1000,
    loss="softmax",
    pretrained=True
)
reid_model.to(device).eval()

reid_transforms = T.Compose([
    T.ToPILImage(),
    T.Resize((256, 128)),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

_pose_estimator = None
_global_lock = threading.Lock()

person_db: Dict[int, Dict[str, Any]] = {}
track_to_person: Dict[Tuple[str, int], Dict[str, Any]] = {}
next_person_id = 1

POSE_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,7),
    (0,4),(4,5),(5,6),(6,8),
    (9,10),
    (11,12),
    (11,13),(13,15),
    (12,14),(14,16),
    (15,17),(15,19),(15,21),
    (16,18),(16,20),(16,22),
    (11,23),(12,24),
    (23,24),
    (23,25),(25,27),(27,29),(29,31),
    (24,26),(26,28),(28,30),(30,32),
]

CAM_COLORS = [
    (0, 255, 0),
    (255, 180, 0),
    (0, 220, 255),
    (255, 0, 180),
    (180, 255, 0),
    (0, 140, 255),
    (255, 80, 80),
    (120, 255, 120),
    (180, 180, 255),
    (255, 220, 120),
    (120, 255, 255),
    (220, 120, 255),
]


def now_ts() -> float:
    return time.time()


def get_pose_estimator():
    global _pose_estimator
    if _pose_estimator is None:
        if not POSE_TASK_PATH.exists():
            raise FileNotFoundError(f"找不到 MediaPipe task 檔案: {POSE_TASK_PATH}")

        options = PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(POSE_TASK_PATH)),
            running_mode=VisionRunningMode.IMAGE
        )
        _pose_estimator = PoseLandmarker.create_from_options(options)
    return _pose_estimator


def reset_global_state():
    global person_db, track_to_person, next_person_id
    with _global_lock:
        person_db = {}
        track_to_person = {}
        next_person_id = 1


def open_camera(source: str):
    try:
        idx = int(source)
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
    except ValueError:
        cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        return None
    return cap


def save_snapshot(task_id: str, cam_name: str, frame: np.ndarray):
    path = SNAPSHOT_DIR / f"{task_id}_{cam_name}_latest.jpg"
    cv2.imwrite(str(path), frame)


def l2_normalize(vec: np.ndarray, eps: float = 1e-12):
    norm = np.linalg.norm(vec)
    if norm < eps:
        return vec
    return vec / norm


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a = l2_normalize(a)
    b = l2_normalize(b)
    return float(np.dot(a, b))


def safe_crop(frame: np.ndarray, box: List[int]):
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = box
    x1 = max(0, min(w - 1, x1))
    x2 = max(0, min(w - 1, x2))
    y1 = max(0, min(h - 1, y1))
    y2 = max(0, min(h - 1, y2))
    if x2 <= x1 or y2 <= y1:
        return None
    crop = frame[y1:y2, x1:x2]
    return crop if crop.size > 0 else None


def crop_quality_ok(crop: Optional[np.ndarray]) -> bool:
    if crop is None or crop.size == 0:
        return False

    h, w = crop.shape[:2]
    if h < MIN_CROP_H or w < MIN_CROP_W:
        return False

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
    if sharpness < MIN_SHARPNESS:
        return False

    return True


def extract_deep_embedding(person_crop: Optional[np.ndarray]):
    if person_crop is None or person_crop.size == 0:
        return None

    if not crop_quality_ok(person_crop):
        return None

    person_crop_rgb = cv2.cvtColor(person_crop, cv2.COLOR_BGR2RGB)
    img_t = reid_transforms(person_crop_rgb).unsqueeze(0).to(device)

    with torch.no_grad():
        emb = reid_model(img_t).squeeze().cpu().numpy()

    return l2_normalize(emb)


def extract_mediapipe_pose(person_crop: Optional[np.ndarray]):
    if person_crop is None or person_crop.size == 0:
        return None

    try:
        estimator = get_pose_estimator()
    except Exception as e:
        print(f"[WARN] PoseLandmarker 初始化失敗: {e}")
        return None

    image_rgb = cv2.cvtColor(person_crop, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
    detection_result = estimator.detect(mp_image)

    if not detection_result.pose_landmarks:
        return None

    landmarks = []
    for lm in detection_result.pose_landmarks[0]:
        landmarks.append([float(lm.x), float(lm.y), float(lm.z)])

    return landmarks


def create_new_person(emb: np.ndarray, camera_name: str) -> int:
    global next_person_id
    pid = next_person_id
    next_person_id += 1

    person_db[pid] = {
        "embeddings": deque([emb], maxlen=MAX_GALLERY_PER_PERSON),
        "skeleton_sequence": deque(maxlen=MAX_SKELETON_SEQ),
        "last_seen": now_ts(),
        "last_camera": camera_name,
        "risk_level": "L0",
        "seen_cameras": {camera_name},
    }
    return pid


def match_existing_person(emb: np.ndarray) -> Tuple[Optional[int], float]:
    best_pid = None
    best_score = -1.0

    for pid, info in person_db.items():
        gallery = info.get("embeddings", [])
        if not gallery:
            continue

        scores = [cosine_similarity(emb, g) for g in gallery]
        if not scores:
            continue

        score = max(scores)
        if score > best_score:
            best_score = score
            best_pid = pid

    if best_pid is not None and best_score >= REID_MATCH_THRESHOLD:
        return best_pid, best_score

    return None, best_score


def resolve_person_id(camera_name: str, track_id: int, emb: np.ndarray) -> Tuple[int, str]:
    key = (camera_name, int(track_id))
    now = now_ts()

    with _global_lock:
        cache = track_to_person.get(key)
        if cache is not None:
            pid = cache["person_id"]
            cache["last_seen"] = now
            if pid in person_db:
                person_db[pid]["last_seen"] = now
                person_db[pid]["last_camera"] = camera_name
                person_db[pid]["seen_cameras"].add(camera_name)
                if emb is not None:
                    person_db[pid]["embeddings"].append(emb)
            return pid, "track-cache"

        matched_pid, score = match_existing_person(emb)

        if matched_pid is not None:
            track_to_person[key] = {
                "person_id": matched_pid,
                "last_seen": now,
            }
            person_db[matched_pid]["last_seen"] = now
            person_db[matched_pid]["last_camera"] = camera_name
            person_db[matched_pid]["seen_cameras"].add(camera_name)
            person_db[matched_pid]["embeddings"].append(emb)
            tag = "reid-strong" if score >= REID_STRONG_THRESHOLD else f"reid:{score:.2f}"
            return matched_pid, tag

        pid = create_new_person(emb, camera_name)
        track_to_person[key] = {
            "person_id": pid,
            "last_seen": now,
        }
        return pid, "new"


def cleanup_stale_tracks():
    now = now_ts()

    with _global_lock:
        stale_track_keys = []
        for key, info in track_to_person.items():
            if now - info.get("last_seen", 0) > TRACK_CACHE_MAX_IDLE_SEC:
                stale_track_keys.append(key)
        for key in stale_track_keys:
            track_to_person.pop(key, None)

        stale_person_ids = []
        for pid, info in person_db.items():
            if now - info.get("last_seen", 0) > PERSON_DB_MAX_IDLE_SEC:
                stale_person_ids.append(pid)
        for pid in stale_person_ids:
            person_db.pop(pid, None)


def update_person_sequence(person_id: int, landmarks: Optional[List[List[float]]]):
    if person_id not in person_db or landmarks is None:
        return
    person_db[person_id]["skeleton_sequence"].append(landmarks)


def draw_pose_on_frame(frame: np.ndarray, box: List[int], landmarks: Optional[List[List[float]]], color=(0, 255, 255)):
    if not landmarks:
        return

    x1, y1, x2, y2 = box
    w = max(1, x2 - x1)
    h = max(1, y2 - y1)

    pts = []
    for lm in landmarks:
        px = int(x1 + lm[0] * w)
        py = int(y1 + lm[1] * h)
        pts.append((px, py))

    for a, b in POSE_CONNECTIONS:
        if a < len(pts) and b < len(pts):
            cv2.line(frame, pts[a], pts[b], color, 2)

    for px, py in pts:
        cv2.circle(frame, (px, py), 2, (255, 255, 0), -1)


def draw_person(
    frame: np.ndarray,
    box: List[int],
    person_id: int,
    track_id: int,
    note: str,
    color=(0, 255, 0),
):
    x1, y1, x2, y2 = box

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

    label_1 = f"PERSON-{person_id}"
    label_2 = f"trk:{track_id} {note}"

    cv2.putText(
        frame,
        label_1,
        (x1, max(22, y1 - 26)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        color,
        2,
    )

    cv2.putText(
        frame,
        label_2,
        (x1, max(22, y1 - 6)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        color,
        2,
    )


def get_cam_color(cam_index: int):
    return CAM_COLORS[cam_index % len(CAM_COLORS)]


def process_camera_frame(
    model: YOLO,
    frame: np.ndarray,
    camera_name: str,
    cam_index: int,
    recorder: Optional[DataRecorder] = None,
    frame_idx: int = 0,
):
    tracker_arg = str(TRACKER_PATH) if TRACKER_PATH.exists() else "bytetrack.yaml"

    results = model.track(
        frame,
        classes=[0],
        conf=CONF_DEFAULT,
        imgsz=IMG_SIZE,
        persist=True,
        tracker=tracker_arg,
        verbose=False,
    )

    result = results[0]
    vis = frame.copy()
    ts = now_ts()
    box_color = get_cam_color(cam_index)

    if result.boxes is None or result.boxes.id is None or len(result.boxes) == 0:
        return vis

    boxes = result.boxes.xyxy.int().cpu().tolist()
    track_ids = result.boxes.id.int().cpu().tolist()
    confs = result.boxes.conf.cpu().tolist()

    for box, track_id, det_conf in zip(boxes, track_ids, confs):
        crop = safe_crop(frame, box)
        emb = extract_deep_embedding(crop)

        if emb is None:
            x1, y1, x2, y2 = box
            cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 180, 255), 2)
            cv2.putText(
                vis,
                "LOW-QUALITY",
                (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 180, 255),
                2,
            )
            continue

        person_id, note = resolve_person_id(camera_name, int(track_id), emb)
        landmarks = extract_mediapipe_pose(crop)

        if landmarks:
            update_person_sequence(person_id, landmarks)
            draw_pose_on_frame(vis, box, landmarks, color=(0, 255, 255))
            seq_len = len(person_db[person_id]["skeleton_sequence"])
            note = f"{note} pose:{seq_len}/150"

        draw_person(
            vis,
            box,
            person_id,
            int(track_id),
            f"{note} c:{det_conf:.2f}",
            color=box_color,
        )

        if recorder is not None:
            recorder.record_frame(
                frame_idx=frame_idx,
                timestamp=ts,
                camera_id=camera_name,
                person_id=int(person_id),
                track_id=int(track_id),
                bbox=box,
                reid_score=float(det_conf),
                landmarks=landmarks,
            )

    return vis


def run_detection_multi_reid(
    sources: List[str],
    conf: float = CONF_DEFAULT,
    task_id: str = "default",
):
    global CONF_DEFAULT
    CONF_DEFAULT = conf
    stop_events[task_id] = False

    if not MODEL_PATH.exists():
        print(f"❌ 找不到 YOLO 權重檔: {MODEL_PATH}")
        stop_events.pop(task_id, None)
        return

    reset_global_state()

    try:
        model = YOLO(str(MODEL_PATH))
        print("✅ YOLO loaded for multi_reid")
    except Exception as e:
        print(f"❌ YOLO 載入失敗: {e}")
        stop_events.pop(task_id, None)
        return

    caps = []
    camera_names = []
    frame_indices = []

    for i, src in enumerate(sources):
        cam_name = f"cam{i}"
        cap = open_camera(src)
        if cap is None:
            print(f"❌ 無法開啟來源: {src} ({cam_name})")
            for opened in caps:
                opened.release()
            stop_events.pop(task_id, None)
            return
        caps.append(cap)
        camera_names.append(cam_name)
        frame_indices.append(0)

    recorder = None
    try:
        recorder = DataRecorder(base_dir=str(BASE_DIR), session_name=task_id)
        print("✅ DataRecorder initialized")
    except Exception as e:
        print(f"❌ DataRecorder 初始化失敗: {e}")
        for cap in caps:
            cap.release()
        stop_events.pop(task_id, None)
        return

    prev_time = now_ts()

    try:
        while not stop_events.get(task_id, False):
            frames = []
            ok_all = True

            for cap in caps:
                ret, frame = cap.read()
                if not ret:
                    ok_all = False
                    break
                frames.append(frame)

            if not ok_all:
                print("[multi_reid] 有鏡頭讀取失敗，任務結束")
                break

            for i, frame in enumerate(frames):
                cam_name = camera_names[i]
                vis = process_camera_frame(
                    model=model,
                    frame=frame,
                    camera_name=cam_name,
                    cam_index=i,
                    recorder=recorder,
                    frame_idx=frame_indices[i],
                )

                now = now_ts()
                fps = 1.0 / max(now - prev_time, 1e-6)
                prev_time = now

                cv2.putText(
                    vis,
                    f"{cam_name.upper()} FPS:{fps:.1f}",
                    (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 255, 0),
                    2,
                )

                save_snapshot(task_id, cam_name, vis)
                frame_indices[i] += 1

            cleanup_stale_tracks()
            time.sleep(0.01)

    except Exception as e:
        print(f"⚠️ multi_reid 偵測過程中發生錯誤: {repr(e)}")
    finally:
        for cap in caps:
            try:
                cap.release()
            except Exception:
                pass

        cv2.destroyAllWindows()
        stop_events.pop(task_id, None)

        if recorder is not None:
            try:
                recorder.finalize()
            except Exception as e:
                print(f"⚠️ recorder.finalize() 失敗: {e}")

        print(f"[multi_reid] 任務 {task_id} 已安全結束")