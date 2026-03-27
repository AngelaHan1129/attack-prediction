from ultralytics import YOLO
import cv2
import numpy as np
import time
from collections import deque
import os

# =========================
# 設定區
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # 取得 backend 目錄
MODEL_PATH = os.path.join(BASE_DIR, "weights", "yolo26n.pt")
# TRACKER_PATH = "custom_botsort.yaml"

CAMERA_0 = 0
CAMERA_1 = 1
CAM_BACKEND = cv2.CAP_DSHOW

CONF = 0.45
IMG_SIZE = 640

# person_id 比對參數
SIM_THRESHOLD = 0.82          # 越高越嚴格
RECENT_BONUS_SEC = 10         # 最近出現的人可稍微放寬
LONG_TERM_TIMEOUT_SEC = 1800  # 30 分鐘不出現才刪掉
MAX_GALLERY_PER_PERSON = 8    # 每個人保存幾組特徵
MIN_BOX_AREA = 4000           # 過小的人框不做 ReID
MAX_COSINE_FOR_SAME = 0.18    # 真 ReID版會用到，簡易版先保留

# 顏色直方圖權重
HIST_WEIGHT = 0.85
SHAPE_WEIGHT = 0.15

# =========================
# 全域資料庫
# =========================
person_db = {}        # person_id -> {embeddings, last_seen, last_camera}
track_to_person = {}  # (camera_name, track_id) -> person_id
next_person_id = 1


# =========================
# 工具函式
# =========================
def now_ts():
    return time.time()


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


def extract_simple_embedding(person_crop):
    """
    簡易版 embedding：
    1. HSV 2D histogram
    2. box shape ratio, brightness
    """
    if person_crop is None or person_crop.size == 0:
        return None

    h, w = person_crop.shape[:2]
    if h * w < MIN_BOX_AREA:
        return None

    resized = cv2.resize(person_crop, (64, 128))
    hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)

    hist = cv2.calcHist([hsv], [0, 1], None, [24, 24], [0, 180, 0, 256])
    hist = cv2.normalize(hist, hist).flatten()

    aspect = np.array([w / max(h, 1)], dtype=np.float32)
    mean_v = np.array([np.mean(hsv[:, :, 2]) / 255.0], dtype=np.float32)
    shape_feat = np.concatenate([aspect, mean_v]).astype(np.float32)
    shape_feat = l2_normalize(shape_feat)

    hist = hist.astype(np.float32)
    hist = l2_normalize(hist)

    emb = np.concatenate([hist * HIST_WEIGHT, shape_feat * SHAPE_WEIGHT]).astype(np.float32)
    emb = l2_normalize(emb)
    return emb


def cleanup_person_db():
    expired = []
    t = now_ts()
    for pid, info in person_db.items():
        if t - info["last_seen"] > LONG_TERM_TIMEOUT_SEC:
            expired.append(pid)

    for pid in expired:
        del person_db[pid]

    expired_tracks = []
    valid_pids = set(person_db.keys())
    for key, pid in track_to_person.items():
        if pid not in valid_pids:
            expired_tracks.append(key)

    for key in expired_tracks:
        del track_to_person[key]


def add_embedding_to_person(person_id, emb, camera_name):
    info = person_db[person_id]
    info["embeddings"].append(emb)
    if len(info["embeddings"]) > MAX_GALLERY_PER_PERSON:
        info["embeddings"].popleft()
    info["last_seen"] = now_ts()
    info["last_camera"] = camera_name


def create_new_person(emb, camera_name):
    global next_person_id
    pid = next_person_id
    next_person_id += 1

    person_db[pid] = {
        "embeddings": deque([emb], maxlen=MAX_GALLERY_PER_PERSON),
        "last_seen": now_ts(),
        "last_camera": camera_name
    }
    return pid


def match_person_id(emb, camera_name):
    """
    從全域 person_db 找最像的人。
    """
    best_pid = None
    best_score = -1.0
    t = now_ts()

    for pid, info in person_db.items():
        gallery = list(info["embeddings"])
        if not gallery:
            continue

        sims = [cosine_similarity(emb, g) for g in gallery]
        score = max(sims)

        # 最近出現者可微幅加分，幫助短時間重入
        dt = t - info["last_seen"]
        if dt < RECENT_BONUS_SEC:
            score += 0.02

        # 不同鏡頭切換可微幅加分，但不要太大，避免誤認
        if info["last_camera"] != camera_name:
            score += 0.01

        if score > best_score:
            best_score = score
            best_pid = pid

    if best_pid is not None and best_score >= SIM_THRESHOLD:
        return best_pid, best_score

    return None, best_score


def resolve_person_id(camera_name, track_id, emb):
    """
    先看這個 track_id 在此鏡頭是否已有映射，
    沒有再去 person_db 找相似的人。
    """
    key = (camera_name, int(track_id))

    if key in track_to_person:
        pid = track_to_person[key]
        if pid in person_db:
            add_embedding_to_person(pid, emb, camera_name)
            return pid, "track-cache"

    pid, score = match_person_id(emb, camera_name)
    if pid is not None:
        track_to_person[key] = pid
        add_embedding_to_person(pid, emb, camera_name)
        return pid, f"matched:{score:.3f}"

    pid = create_new_person(emb, camera_name)
    track_to_person[key] = pid
    return pid, "new"


def draw_person(frame, box, person_id, track_id, note, color=(0, 255, 0)):
    x1, y1, x2, y2 = box
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

    text1 = f"PERSON-{person_id}"
    text2 = f"track:{track_id} {note}"

    cv2.putText(frame, text1, (x1, max(20, y1 - 28)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)
    cv2.putText(frame, text2, (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)



def process_camera_frame(model, frame, camera_name):
    results = model.track(
        frame,
        classes=[0],
        conf=CONF,
        imgsz=IMG_SIZE,
        persist=True,           
        tracker="bytetrack.yaml",
        verbose=False
    )

    result = results[0]
    vis = frame.copy()

    # 確保有 boxes 且有 track id
    if result.boxes is None or result.boxes.id is None:
        return vis

    boxes     = result.boxes.xyxy.int().cpu().tolist()
    track_ids = result.boxes.id.int().cpu().tolist()  # ← 真正的 Track ID
    confs     = result.boxes.conf.cpu().tolist()

    for box, track_id, conf in zip(boxes, track_ids, confs):
        crop = safe_crop(frame, box)
        emb  = extract_simple_embedding(crop)

        if emb is None:
            x1, y1, x2, y2 = box
            cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 180, 255), 2)
            continue

        person_id, note = resolve_person_id(camera_name, track_id, emb)
        draw_person(vis, box, person_id, track_id, f"{note} c:{conf:.2f}")

    return vis

def open_camera(index):
    cap = cv2.VideoCapture(index, CAM_BACKEND)
    if not cap.isOpened():
        return None
    return cap


def main():
    model = YOLO(MODEL_PATH)

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

        cleanup_person_db()

        out1 = process_camera_frame(model, frame1, "cam0")
        out2 = process_camera_frame(model, frame2, "cam1")

        now = time.time()
        fps = 1.0 / max(now - prev_time, 1e-6)
        prev_time = now

        cv2.putText(out1, f"cam0 FPS:{fps:.1f}", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        cv2.putText(out2, f"cam1 FPS:{fps:.1f}", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

        combined = np.hstack([
            cv2.resize(out1, (640, 480)),
            cv2.resize(out2, (640, 480))
        ])

        cv2.imshow("Cross-Camera ReID - Simple", combined)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    cap1.release()
    cap2.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()