import time
from pathlib import Path
from collections import deque

import cv2
import numpy as np
import torch
import torchvision.transforms as T
import mediapipe as mp
import torchreid

from ultralytics import YOLO

from app.core.cv.pipelines.detect import stop_events


BASE_DIR = Path(__file__).resolve().parents[4]   # backend/
SNAPSHOT_DIR = BASE_DIR / "data" / "snapshots"
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = BASE_DIR / "weights" / "yolo26n.pt"
POSE_TASK_PATH = BASE_DIR / "weights" / "pose_landmarker_lite.task"
TRACKER_PATH = BASE_DIR / "app" / "scripts" / "custom_tracker.yaml"

CONF = 0.45
IMG_SIZE = 640
MAX_GALLERY_PER_PERSON = 8

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

pose_estimator = None
person_db = {}
track_to_person = {}
next_person_id = 1


def now_ts():
    return time.time()


def get_pose_estimator():
    global pose_estimator

    if pose_estimator is None:
        if not POSE_TASK_PATH.exists():
            raise FileNotFoundError(f"找不到 MediaPipe task 檔案: {POSE_TASK_PATH}")

        options = PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(POSE_TASK_PATH)),
            running_mode=VisionRunningMode.IMAGE
        )
        pose_estimator = PoseLandmarker.create_from_options(options)

    return pose_estimator


def open_camera(source):
    source = int(source) if str(source).isdigit() else source
    cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
    if not cap.isOpened():
        return None
    return cap


def save_snapshot(task_id: str, cam: str, frame):
    path = SNAPSHOT_DIR / f"{task_id}_{cam}_latest.jpg"
    cv2.imwrite(str(path), frame)


def l2_normalize(vec, eps=1e-12):
    norm = np.linalg.norm(vec)
    if norm < eps:
        return vec
    return vec / norm


def cosine_similarity(a, b):
    a = l2_normalize(a)
    b = l2_normalize(b)
    return float(np.dot(a, b))


def safe_crop(frame, box):
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


def extract_deep_embedding(person_crop):
    if person_crop is None or person_crop.size == 0:
        return None

    h, w = person_crop.shape[:2]
    if h < 120 or w < 60:
        return None

    person_crop_rgb = cv2.cvtColor(person_crop, cv2.COLOR_BGR2RGB)
    img_t = reid_transforms(person_crop_rgb).unsqueeze(0).to(device)

    with torch.no_grad():
        emb = reid_model(img_t).squeeze().cpu().numpy()

    return l2_normalize(emb)


def extract_mediapipe_pose(person_crop):
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
        landmarks.append([lm.x, lm.y, lm.z])

    return landmarks


def create_new_person(emb, camera_name):
    global next_person_id
    pid = next_person_id
    next_person_id += 1

    person_db[pid] = {
        "embeddings": deque([emb], maxlen=MAX_GALLERY_PER_PERSON),
        "skeleton_sequence": deque(maxlen=150),
        "last_seen": now_ts(),
        "last_camera": camera_name,
        "risk_level": "L0",
    }
    return pid


def resolve_person_id(camera_name, track_id, emb):
    key = (camera_name, int(track_id))

    if key in track_to_person:
        return track_to_person[key], "track-cache"

    pid = create_new_person(emb, camera_name)
    track_to_person[key] = pid
    return pid, "new"


def update_person_sequence(person_id, landmarks):
    info = person_db[person_id]
    info["skeleton_sequence"].append(landmarks)


def draw_person(frame, box, person_id, track_id, note, color=(0, 255, 0)):
    x1, y1, x2, y2 = box
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    cv2.putText(
        frame,
        f"PERSON-{person_id}",
        (x1, max(20, y1 - 28)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        color,
        2,
    )
    cv2.putText(
        frame,
        f"track:{track_id} {note}",
        (x1, max(20, y1 - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        color,
        2,
    )


def process_camera_frame(model, frame, camera_name):
    tracker_arg = str(TRACKER_PATH) if TRACKER_PATH.exists() else "bytetrack.yaml"

    results = model.track(
        frame,
        classes=[0],
        conf=CONF,
        imgsz=IMG_SIZE,
        persist=True,
        tracker=tracker_arg,
        verbose=False
    )

    result = results[0]
    vis = frame.copy()

    if result.boxes is None or result.boxes.id is None:
        return vis

    boxes = result.boxes.xyxy.int().cpu().tolist()
    track_ids = result.boxes.id.int().cpu().tolist()
    confs = result.boxes.conf.cpu().tolist()

    for box, track_id, conf in zip(boxes, track_ids, confs):
        crop = safe_crop(frame, box)
        emb = extract_deep_embedding(crop)

        if emb is None:
            x1, y1, x2, y2 = box
            cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 180, 255), 2)
            continue

        person_id, note = resolve_person_id(camera_name, track_id, emb)

        if person_id is None:
            continue

        landmarks = extract_mediapipe_pose(crop)
        if landmarks:
            update_person_sequence(person_id, landmarks)
            seq_len = len(person_db[person_id]["skeleton_sequence"])
            note += f" | seq:{seq_len}/150"

        draw_person(vis, box, person_id, track_id, f"{note} c:{conf:.2f}")

    return vis


def run_detection_dual_reid(source0="0", source1="1", conf=0.5, task_id="default"):
    global CONF
    CONF = conf

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"找不到 YOLO 權重檔: {MODEL_PATH}")

    model = YOLO(str(MODEL_PATH))

    cap0 = open_camera(source0)
    cap1 = open_camera(source1)

    if cap0 is None or cap1 is None:
        stop_events.pop(task_id, None)
        return

    try:
        while not stop_events.get(task_id, False):
            ret0, frame0 = cap0.read()
            ret1, frame1 = cap1.read()

            if not ret0 or not ret1:
                break

            out0 = process_camera_frame(model, frame0, "cam0")
            out1 = process_camera_frame(model, frame1, "cam1")

            save_snapshot(task_id, "cam0", out0)
            save_snapshot(task_id, "cam1", out1)

            time.sleep(0.03)

    finally:
        cap0.release()
        cap1.release()
        stop_events.pop(task_id, None)