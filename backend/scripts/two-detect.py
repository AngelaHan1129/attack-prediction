from ultralytics import YOLO
import cv2
import numpy as np
import time
from collections import deque
import os

# === 新增：深度學習 ReID 模組匯入 ===
import torch
import torchvision.transforms as T
from torchvision.models import resnet50, ResNet50_Weights
import torch.nn as nn
import torchreid
import mediapipe as mp

# === 替換為專門針對行人 ReID 訓練的模型 ===
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"🔄 ReID 模型使用硬體加速: {device}")

# 使用內建的 ResNet50
# reid_model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)
# reid_model.fc = nn.Identity()  # 拔除最後的分類層，改為輸出 2048 維特徵向量
# reid_model.to(device).eval()   # 設定為評估模式

# 初始化專為行人重識別設計的 OSNet (這非常輕量且對跨鏡頭極強)
reid_model = torchreid.models.build_model(
    name='osnet_x1_0', 
    num_classes=1000, 
    loss='softmax', 
    pretrained=True
)
reid_model.to(device).eval()

# OSNet 的預設前處理
reid_transforms = T.Compose([
    T.ToPILImage(),
    T.Resize((256, 128)),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])
# ===  MediaPipe Tasks API ===
BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

# 建立 PoseLandmarker 設定
options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path='pose_landmarker_lite.task'), # 使用最輕量級模型
    running_mode=VisionRunningMode.IMAGE
)
# 初始化模型
pose_estimator = PoseLandmarker.create_from_options(options)

# =========================
# 設定區
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # 取得 backend 目錄
MODEL_PATH = os.path.join(BASE_DIR, "weights", "yolo26n.pt")
TRACKER_PATH = os.path.join(BASE_DIR, "scripts", "custom_tracker.yaml")

CAMERA_0 = 0
CAMERA_1 = 1
CAM_BACKEND = cv2.CAP_DSHOW

CONF = 0.45
IMG_SIZE = 640

# person_id 比對參數
SIM_THRESHOLD = 0.85     # 越高越嚴格
RECENT_BONUS_SEC = 5         # 最近出現的人可稍微放寬
LONG_TERM_TIMEOUT_SEC = 1800  # 30 分鐘不出現才刪掉
MAX_GALLERY_PER_PERSON = 8    # 每個人保存幾組特徵
MIN_BOX_AREA = 4000           # 過小的人框不做 ReID
MAX_COSINE_FOR_SAME = 0.30    # 真 ReID版會用到，簡易版先保留

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


def extract_deep_embedding(person_crop):
    if person_crop is None or person_crop.size == 0:
        return None

    h, w = person_crop.shape[:2]
    # 【大幅提高面積門檻】
    # 如果寬度小於 60 或高度小於 120，代表這張圖太模糊，拒絕提取特徵
    # 這能極大程度避免垃圾特徵產生新的錯誤 ID
    if h < 120 or w < 60:  
        return None

    person_crop_rgb = cv2.cvtColor(person_crop, cv2.COLOR_BGR2RGB)
    img_t = reid_transforms(person_crop_rgb).unsqueeze(0).to(device)
    
    with torch.no_grad():
        emb = reid_model(img_t).squeeze().cpu().numpy()
        
    return l2_normalize(emb)

def extract_mediapipe_pose(person_crop):
    """
    從裁切出的人物影像中提取 33 個 3D 骨架關鍵點 (使用新版 Tasks API)
    """
    if person_crop is None or person_crop.size == 0:
        return None

    # OpenCV BGR 轉 RGB
    image_rgb = cv2.cvtColor(person_crop, cv2.COLOR_BGR2RGB)
    
    # 轉換成 MediaPipe 專用的 Image 格式
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
    
    # 執行預測
    detection_result = pose_estimator.detect(mp_image)

    # 檢查是否有抓到骨架 (如果畫面中沒人或太模糊會是空的)
    if not detection_result.pose_landmarks:
        return None

    # 取第一個人 (裁切框裡面通常只有一個人) 的 33 個點
    landmarks = []
    for lm in detection_result.pose_landmarks[0]:
        landmarks.append([lm.x, lm.y, lm.z])
        
    return landmarks

def update_person_sequence(person_id, landmarks):
    """
    更新該人物的滑動視窗 (150幀)。
    當集滿 150 幀時，模擬觸發意圖預測模組。
    """
    info = person_db[person_id]
    info["skeleton_sequence"].append(landmarks)
    
    # 若集滿 150 幀 (相當於 30FPS 下的 5 秒)，觸發預測並滑動
    if len(info["skeleton_sequence"]) == 150:
        # TODO: 這裡未來要接入 ST-GCN + LSTM 模型
        # intent_scores = predict_intent(list(info["skeleton_sequence"]))
        # risk_level = calculate_ahp_risk(intent_scores)
        
        print(f"🚨 [預測觸發] Person-{person_id} 已收集 150 幀骨架序列，執行意圖預測！")
        
        # 滑動視窗：移除最舊的 15 幀 (半秒)，讓下次能持續滾動預測
        for _ in range(15):
            info["skeleton_sequence"].popleft()

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
    gallery = info["embeddings"]
    t = now_ts()

    # 【新增冷卻時間】同一人在同一個鏡頭，每 0.5 秒只更新一次特徵庫
    # 避免短時間內的連續模糊幀把記憶庫洗壞
    if len(gallery) > 0 and camera_name == info["last_camera"]:
        if t - info["last_seen"] < 0.5:
            info["last_seen"] = t
            return  # 提早結束，不更新特徵

    if len(gallery) == 0:
        gallery.append(emb)
    else:
        sims = [cosine_similarity(emb, g) for g in gallery]
        max_sim = max(sims)
        max_idx = sims.index(max_sim)

        if max_sim > 0.85:
            alpha = 0.90  # 提高 EMA 權重，盡量保留舊的清晰特徵
            fused = alpha * gallery[max_idx] + (1.0 - alpha) * emb
            gallery[max_idx] = l2_normalize(fused)
        else:
            gallery.append(emb)

    info["last_seen"] = t
    info["last_camera"] = camera_name


def create_new_person(emb, camera_name):
    global next_person_id
    pid = next_person_id
    next_person_id += 1

    person_db[pid] = {
        "embeddings": deque([emb], maxlen=MAX_GALLERY_PER_PERSON),
        "skeleton_sequence": deque(maxlen=150), # 新增：150 幀滑動視窗
        "last_seen": now_ts(),
        "last_camera": camera_name,
        "risk_level": "L0"  # 新增：預設風險等級
    }
    return pid

def match_person_id(emb, camera_name):
    best_pid = None
    best_score = -1.0
    t = now_ts()

    for pid, info in person_db.items():
        gallery = list(info["embeddings"])
        if not gallery:
            continue

        # 1. 算出當前影像與這號人物在記憶庫中所有視角的相似度
        sims = [cosine_similarity(emb, g) for g in gallery]
        base_score = max(sims)
        
        # 2. 判斷是否為跨鏡頭
        is_cross_camera = (info["last_camera"] != camera_name)

        # 3. 跨鏡頭時間補償：如果這個人剛在別的鏡頭消失 (30秒內)，
        # 給予高額加分，因為他極高機率是走過來了。
        dt = t - info["last_seen"]
        if is_cross_camera and dt < 30:
            base_score += 0.08  # 加大跨鏡頭的過渡期補償
            
        final_score = min(1.0, base_score)

        if final_score > best_score:
            best_score = final_score
            best_pid = pid

    if best_pid is not None:
        # 【重要修改：大幅放寬跨鏡頭的門檻】
        # OSNet 的跨鏡頭分數有時候會掉到 0.6 左右
        is_cross = (person_db[best_pid]["last_camera"] != camera_name)
        threshold = 0.65 if is_cross else 0.82
        
        prefix = "[跨鏡比對]" if is_cross else "[同鏡比對]"
        print(f"🔍 {prefix} 目標與 ID={best_pid} 最像, 分數={best_score:.3f} (門檻:{threshold})")
        
        if best_score >= threshold:
            return best_pid, best_score
        else:
            print(f"❌ 分數 {best_score:.3f} 低於門檻 {threshold}，分配新 ID！")

    return None, best_score


def resolve_person_id(camera_name, track_id, emb):
    key = (camera_name, int(track_id))

    # 1. 如果這個 track_id 已經有對應的全域 person_id，直接沿用，不要重新比對
    if key in track_to_person:
        pid = track_to_person[key]
        if pid in person_db:
            if emb is not None:
                add_embedding_to_person(pid, emb, camera_name)
            return pid, "track-cache"

    # 2. 只有當這是「全新出現的 track_id」時，才進行 ReID 比對
    if emb is None:
        return None, "no-emb" # 沒有特徵就不分配新 ID

    pid, score = match_person_id(emb, camera_name)
    
    if pid is not None:
        track_to_person[key] = pid
        add_embedding_to_person(pid, emb, camera_name)
        return pid, f"matched:{score:.3f}"

    # 3. 真的找不到相似的人，才創建新 ID
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
        tracker="bytetrack.yaml", # 或使用你的 custom_tracker.yaml
        verbose=False
    )

    result = results[0]
    vis = frame.copy()

    if result.boxes is None or result.boxes.id is None:
        return vis

    boxes     = result.boxes.xyxy.int().cpu().tolist()
    track_ids = result.boxes.id.int().cpu().tolist()  
    confs     = result.boxes.conf.cpu().tolist()

    for box, track_id, conf in zip(boxes, track_ids, confs):
        crop = safe_crop(frame, box)
        
        # 1. 深度特徵提取
        emb = extract_deep_embedding(crop)

        if emb is None:
            x1, y1, x2, y2 = box
            cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 180, 255), 2)
            continue

        # 2. 跨鏡頭 ReID 取得全域 person_id
        person_id, note = resolve_person_id(camera_name, track_id, emb)
        
        # 如果因為太小而沒有分配到 ID，跳過畫框與後續處理
        if person_id is None:
            continue

        # 3. MediaPipe 骨架提取與滑動視窗更新
        landmarks = extract_mediapipe_pose(crop)
        if landmarks:
            update_person_sequence(person_id, landmarks)
            # 在畫面上標註他目前的收集進度
            seq_len = len(person_db[person_id]["skeleton_sequence"])
            note += f" | seq:{seq_len}/150"
        
        # 4. 畫框
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