import os
import json
import time
import datetime
from typing import Optional, List, Dict, Any

import numpy as np


class DataRecorder:
    """
    收集每幀的偵測結果，並自動切出 150 幀的滑動視窗，輸出：
    - data/sessions/{session}/frames.jsonl
    - data/sessions/{session}/windows.jsonl
    - data/sessions/{session}/pose/person_x/*.npy
    """

    def __init__(self, base_dir: str, session_name: Optional[str] = None):
        self.base_dir = base_dir
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_name = session_name or f"session_{ts}"

        self.session_dir = os.path.join(self.base_dir, "data", "sessions", self.session_name)
        os.makedirs(self.session_dir, exist_ok=True)

        self.frames_path = os.path.join(self.session_dir, "frames.jsonl")
        self.windows_path = os.path.join(self.session_dir, "windows.jsonl")

        self.frames_file = open(self.frames_path, "w", encoding="utf-8")
        self.windows_file = open(self.windows_path, "w", encoding="utf-8")

        # 每個 person_id 的滑動視窗 buffer：frame 索引 -> 單幀資料
        self.person_buffers: Dict[int, List[Dict[str, Any]]] = {}
        self.window_index: Dict[int, int] = {}  # person_id -> 下一個 window 序號

        self.start_time = time.time()
        self.total_frames = 0

    # =========================
    # 公開 API：每幀呼叫一次
    # =========================
    def record_frame(
        self,
        frame_idx: int,
        timestamp: float,
        camera_id: str,
        person_id: int,
        track_id: int,
        bbox: List[int],
        reid_score: float,
        landmarks: Optional[List[List[float]]] = None,
    ):
        """
        寫一行 frames.jsonl，並更新該 person 的滑動視窗 buffer。
        landmarks: 33x3 或 None
        """
        self.total_frames += 1

        frame_record = {
            "frame_idx": frame_idx,
            "timestamp": timestamp,
            "camera_id": camera_id,
            "person_id": int(person_id),
            "track_id": int(track_id),
            "bbox": bbox,
            "reid_score": float(reid_score),
            "has_pose": landmarks is not None,
            "landmarks": landmarks,
        }
        self.frames_file.write(json.dumps(frame_record, ensure_ascii=False) + "\n")

        # 更新該 person 的 buffer
        if person_id not in self.person_buffers:
            self.person_buffers[person_id] = []
            self.window_index[person_id] = 0

        self.person_buffers[person_id].append(frame_record)

        # 只保留最近 150 幀
        if len(self.person_buffers[person_id]) > 150:
            self.person_buffers[person_id].pop(0)

        # 當累積到 150 幀，就切一個 window
        if len(self.person_buffers[person_id]) == 150:
            self._emit_window(person_id)

    # =========================
    # 內部：切 window + 存 .npy
    # =========================
    def _emit_window(self, person_id: int):
        buf = self.person_buffers[person_id]
        if len(buf) < 150:
            return

        win_idx = self.window_index[person_id]
        self.window_index[person_id] += 1

        start = buf[0]
        end = buf[-1]

        # 組 pose tensor (150, 33, 3) 與 mask (150,)
        T = len(buf)
        pose = np.zeros((T, 33, 3), dtype=np.float32)
        mask = np.zeros((T,), dtype=np.float32)

        has_pose_count = 0
        reid_scores = []

        for i, rec in enumerate(buf):
            reid_scores.append(float(rec.get("reid_score", 0.0)))
            if rec.get("has_pose") and rec.get("landmarks"):
                lm = np.array(rec["landmarks"], dtype=np.float32)
                if lm.shape == (33, 3):
                    pose[i] = lm
                    mask[i] = 1.0
                    has_pose_count += 1

        pose_valid_ratio = has_pose_count / float(T) if T > 0 else 0.0
        avg_reid_score = float(np.mean(reid_scores)) if reid_scores else 0.0

        # 存成 .npy
        pose_dir = os.path.join(self.session_dir, "pose", f"person_{person_id}")
        os.makedirs(pose_dir, exist_ok=True)

        window_id = f"{self.session_name}_p{person_id}_w{win_idx:05d}"
        pose_path = os.path.join(pose_dir, f"{window_id}_pose.npy")
        mask_path = os.path.join(pose_dir, f"{window_id}_mask.npy")

        np.save(pose_path, pose)
        np.save(mask_path, mask)

        # 寫一行 windows.jsonl（預留標註欄位）
        win_record = {
            "window_id": window_id,
            "person_id": int(person_id),
            "start_frame": start["frame_idx"],
            "end_frame": end["frame_idx"],
            "start_ts": start["timestamp"],
            "end_ts": end["timestamp"],
            "camera_ids": list({r["camera_id"] for r in buf}),
            "pose_valid_ratio": pose_valid_ratio,
            "avg_reid_score": avg_reid_score,
            "pose_npy": os.path.relpath(pose_path, self.base_dir).replace("\\", "/"),
            "mask_npy": os.path.relpath(mask_path, self.base_dir).replace("\\", "/"),
            "action_label": None,
            "risk_label": None,
            "next_risk": None,
        }
        self.windows_file.write(json.dumps(win_record, ensure_ascii=False) + "\n")

        # 滑動視窗：移除最前面的 15 幀
        for _ in range(15):
            if self.person_buffers[person_id]:
                self.person_buffers[person_id].pop(0)

    # =========================
    # 結束：關檔 + meta.json
    # =========================
    def finalize(self):
        if not self.frames_file.closed:
            self.frames_file.close()
        if not self.windows_file.closed:
            self.windows_file.close()

        meta = {
            "session_name": self.session_name,
            "created_at": time.time(),
            "duration_sec": time.time() - self.start_time,
            "total_frames": self.total_frames,
            "persons": sorted(self.person_buffers.keys()),
        }
        meta_path = os.path.join(self.session_dir, "meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)