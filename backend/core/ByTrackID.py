from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path
import time

model = YOLO("yolo26n.pt")

tracker_path = "botsort.yaml"  # 先用內建，穩定後再改 custom_botsort.yaml

# 你的固定身份資料庫
person_db = {}          # person_id -> {"embedding": np.array, "last_seen": float}
track_to_person = {}    # track_id -> person_id
next_person_id = 1

MAX_PERSON_GAP_SEC = 30        # 一個身份最多保留多久沒出現
SIMILARITY_THRESHOLD = 0.75    # 越高越嚴格，0.7~0.9 可慢慢調


def extract_embedding(frame, box):
    x1, y1, x2, y2 = box
    h, w = frame.shape[:2]

    x1 = max(0, min(x1, w - 1))
    y1 = max(0, min(y1, h - 1))
    x2 = max(0, min(x2, w - 1))
    y2 = max(0, min(y2, h - 1))

    if x2 <= x1 or y2 <= y1:
        return None

    crop = frame[y1:y2, x1:x2]
    if crop.size == 0:
        return None

    crop = cv2.resize(crop, (64, 128))
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

    hist_h = cv2.calcHist([hsv], [0], None, [32], [0, 180])
    hist_s = cv2.calcHist([hsv], [1], None, [32], [0, 256])
    hist_v = cv2.calcHist([hsv], [2], None, [32], [0, 256])

    feat = np.concatenate([hist_h.flatten(), hist_s.flatten(), hist_v.flatten()]).astype(np.float32)
    norm = np.linalg.norm(feat)
    if norm == 0:
        return None
    feat /= norm
    return feat


def cosine_similarity(a, b):
    return float(np.dot(a, b))


def cleanup_old_person_db():
    now = time.time()
    expired = []
    for person_id, info in person_db.items():
        if now - info["last_seen"] > MAX_PERSON_GAP_SEC:
            expired.append(person_id)

    for person_id in expired:
        del person_db[person_id]

    invalid_tracks = []
    for track_id, person_id in track_to_person.items():
        if person_id not in person_db:
            invalid_tracks.append(track_id)

    for track_id in invalid_tracks:
        del track_to_person[track_id]


def assign_person_id(track_id, embedding):
    global next_person_id

    now = time.time()

    # 如果這個 track 已經配對過固定身份，直接延用
    if track_id in track_to_person:
        person_id = track_to_person[track_id]
        if person_id in person_db:
            old_emb = person_db[person_id]["embedding"]
            person_db[person_id]["embedding"] = 0.7 * old_emb + 0.3 * embedding
            person_db[person_id]["embedding"] /= np.linalg.norm(person_db[person_id]["embedding"])
            person_db[person_id]["last_seen"] = now
            return person_id

    # 否則去資料庫找最像的人
    best_person_id = None
    best_score = -1.0

    for person_id, info in person_db.items():
        score = cosine_similarity(embedding, info["embedding"])
        if score > best_score:
            best_score = score
            best_person_id = person_id

    # 相似度夠高，視為同一人
    if best_person_id is not None and best_score >= SIMILARITY_THRESHOLD:
        track_to_person[track_id] = best_person_id
        old_emb = person_db[best_person_id]["embedding"]
        person_db[best_person_id]["embedding"] = 0.7 * old_emb + 0.3 * embedding
        person_db[best_person_id]["embedding"] /= np.linalg.norm(person_db[best_person_id]["embedding"])
        person_db[best_person_id]["last_seen"] = now
        return best_person_id

    # 否則建立新身份
    person_id = next_person_id
    next_person_id += 1
    person_db[person_id] = {
        "embedding": embedding,
        "last_seen": now
    }
    track_to_person[track_id] = person_id
    return person_id


for i in range(5):
    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
    if cap.isOpened():
        print(f"鏡頭 {i} OK!")
        break
else:
    print("無鏡頭！用影片測試")
    cap = cv2.VideoCapture("test.mp4")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("讀取失敗")
        break

    cleanup_old_person_db()

    results = model.track(
        frame,
        classes=[0],
        conf=0.5,
        persist=True,
        tracker=tracker_path
    )

    result = results[0]

    if result.boxes is not None and result.boxes.id is not None:
        boxes = result.boxes.xyxy.cpu().numpy().astype(int)
        track_ids = result.boxes.id.int().cpu().tolist()
        confs = result.boxes.conf.cpu().tolist()

        for box, track_id, conf in zip(boxes, track_ids, confs):
            x1, y1, x2, y2 = box

            embedding = extract_embedding(frame, (x1, y1, x2, y2))
            if embedding is None:
                continue

            person_id = assign_person_id(track_id, embedding)

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                frame,
                f"PERSON-{person_id}  track:{track_id}  {conf:.2f}",
                (x1, max(0, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2
            )

    cv2.imshow("YOLO + Tracker + Person ID", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
