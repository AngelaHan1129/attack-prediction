# backend/app/core/cv/reid.py

import time
from collections import deque

import cv2
import numpy as np

# ===== 參數 =====
SIM_THRESHOLD = 0.82
RECENT_BONUS_SEC = 10
LONG_TERM_TIMEOUT_SEC = 1800
MAX_GALLERY_PER_PERSON = 8
MIN_BOX_AREA = 4000


def l2_normalize(vec, eps=1e-12):
    norm = np.linalg.norm(vec)
    if norm < eps:
        return vec
    return vec / norm


def cosine_similarity(a, b):
    a = l2_normalize(a)
    b = l2_normalize(b)
    return float(np.dot(a, b))


# ======= ReID 特徵提取（暫時用簡單版本） =======
class ReIDExtractor:
    """
    暫時版本：用 HSV 直方圖 + 形狀特徵當 embedding。
    之後你要換成 TorchReID，只要改 extract() 的實作即可。
    """
    def __init__(self):
        pass

    def extract(self, crop_bgr: np.ndarray):
        if crop_bgr is None or crop_bgr.size == 0:
            return None

        h, w = crop_bgr.shape[:2]
        if h * w < MIN_BOX_AREA:
            return None

        resized = cv2.resize(crop_bgr, (64, 128))
        hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)

        # 顏色 histogram
        hist = cv2.calcHist([hsv], [0, 1], None, [24, 24], [0, 180, 0, 256])
        hist = cv2.normalize(hist, hist).flatten().astype(np.float32)
        hist = l2_normalize(hist)

        # 長寬比 + 亮度
        aspect = np.array([w / max(h, 1)], dtype=np.float32)
        mean_v = np.array([np.mean(hsv[:, :, 2]) / 255.0], dtype=np.float32)
        shape_feat = np.concatenate([aspect, mean_v]).astype(np.float32)
        shape_feat = l2_normalize(shape_feat)

        emb = np.concatenate([hist, shape_feat]).astype(np.float32)
        emb = l2_normalize(emb)
        return emb


# ======= 全域 ReID 管理 =======
class ReIDGallery:
    def __init__(self):
        # pid -> {embeddings, last_seen, last_camera}
        self.person_db = {}
        # (camera_name, track_id) -> pid
        self.track_to_person = {}
        self.next_person_id = 1

    def cleanup(self):
        """定期清除太久沒出現的人，避免 DB 無限成長。"""
        now = time.time()
        expired = [
            pid for pid, info in self.person_db.items()
            if now - info["last_seen"] > LONG_TERM_TIMEOUT_SEC
        ]
        for pid in expired:
            del self.person_db[pid]

        valid_pids = set(self.person_db.keys())
        self.track_to_person = {
            k: v for k, v in self.track_to_person.items() if v in valid_pids
        }

    def _add_embedding_to_person(self, person_id, emb, camera_name):
        info = self.person_db[person_id]
        info["embeddings"].append(emb)
        if len(info["embeddings"]) > MAX_GALLERY_PER_PERSON:
            info["embeddings"].popleft()
        info["last_seen"] = time.time()
        info["last_camera"] = camera_name

    def _create_new_person(self, emb, camera_name):
        pid = self.next_person_id
        self.next_person_id += 1
        self.person_db[pid] = {
            "embeddings": deque([emb], maxlen=MAX_GALLERY_PER_PERSON),
            "last_seen": time.time(),
            "last_camera": camera_name,
        }
        return pid

    def _match_person_id(self, emb, camera_name):
        best_pid = None
        best_score = -1.0
        now = time.time()

        for pid, info in self.person_db.items():
            gallery = list(info["embeddings"])
            if not gallery:
                continue

            sims = [cosine_similarity(emb, g) for g in gallery]
            score = max(sims)

            dt = now - info["last_seen"]
            if dt < RECENT_BONUS_SEC:
                score += 0.02

            if info["last_camera"] != camera_name:
                score += 0.01

            if score > best_score:
                best_score = score
                best_pid = pid

        if best_pid is not None and best_score >= SIM_THRESHOLD:
            return best_pid, best_score

        return None, best_score

    def resolve(self, camera_name, track_id, emb):
        """
        從 track_id + embedding 決定全域 person_id。
        回傳: (person_id, note)
        """
        key = (camera_name, int(track_id))

        # 1. 先看 track cache
        if key in self.track_to_person:
            pid = self.track_to_person[key]
            if pid in self.person_db:
                self._add_embedding_to_person(pid, emb, camera_name)
                return pid, "track-cache"

        # 2. 用 embedding 在 person_db 裡找最像的
        pid, score = self._match_person_id(emb, camera_name)
        if pid is not None:
            self.track_to_person[key] = pid
            self._add_embedding_to_person(pid, emb, camera_name)
            return pid, f"matched:{score:.3f}"

        # 3. 找不到 → 新建一個人
        pid = self._create_new_person(emb, camera_name)
        self.track_to_person[key] = pid
        return pid, "new"