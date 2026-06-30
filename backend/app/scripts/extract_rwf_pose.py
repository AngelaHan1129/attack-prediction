from __future__ import annotations

import argparse
import json
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np


@dataclass
class SampleItem:
    split: str
    class_name: str
    label: int
    video_path: Path
    rel_stem: str


CLASS_TO_LABEL = {
    "NonFight": 0,
    "Fight": 1,
}

VIDEO_EXTS = {".avi", ".mp4", ".mov", ".mkv", ".webm"}

# MediaPipe Pose 33 landmarks -> COCO-like 17 joints
MP33_TO_COCO17 = [
    0,   # nose
    2,   # left_eye
    5,   # right_eye
    7,   # left_ear
    8,   # right_ear
    11,  # left_shoulder
    12,  # right_shoulder
    13,  # left_elbow
    14,  # right_elbow
    15,  # left_wrist
    16,  # right_wrist
    23,  # left_hip
    24,  # right_hip
    25,  # left_knee
    26,  # right_knee
    27,  # left_ankle
    28,  # right_ankle
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract RWF2000 video skeletons into ST-GCN .npy tensors"
    )
    parser.add_argument(
        "--input-root",
        type=Path,
        default=Path("../STGCN/data/raw"),
        help="Root folder of videos, e.g. ../STGCN/data/raw",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("../STGCN/data/processed"),
        help="Where per-sample .npy tensors are written",
    )
    parser.add_argument(
        "--weights",
        type=Path,
        required=True,
        help="Path to MediaPipe pose landmarker .task file",
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=60,
        help="Number of frames sampled per video",
    )
    parser.add_argument(
        "--max-persons",
        type=int,
        default=2,
        help="Maximum persons (M) kept in output tensor",
    )
    parser.add_argument(
        "--min-visibility",
        type=float,
        default=0.0,
        help="Visibility threshold below which landmark score becomes 0",
    )
    parser.add_argument(
        "--save-meta",
        action="store_true",
        help="Save metadata json alongside each .npy",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Only process first N videos for debugging; 0 = all",
    )
    return parser.parse_args()


def build_sample_list(input_root: Path) -> List[SampleItem]:
    items: List[SampleItem] = []
    for split in ["train", "val", "test"]:
        split_dir = input_root / split
        if not split_dir.exists():
            continue
        for class_name, label in CLASS_TO_LABEL.items():
            class_dir = split_dir / class_name
            if not class_dir.exists():
                continue
            for p in sorted(class_dir.rglob("*")):
                if p.is_file() and p.suffix.lower() in VIDEO_EXTS:
                    rel = p.relative_to(split_dir).with_suffix("")
                    rel_stem = rel.as_posix()
                    items.append(
                        SampleItem(
                            split=split,
                            class_name=class_name,
                            label=label,
                            video_path=p,
                            rel_stem=rel_stem,
                        )
                    )
    return items


def bbox_area_xyxy(box: np.ndarray) -> float:
    x1, y1, x2, y2 = box
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def compute_bbox_from_landmarks(norm_xy: np.ndarray, frame_w: int, frame_h: int) -> np.ndarray:
    xs = np.clip(norm_xy[:, 0], 0.0, 1.0) * frame_w
    ys = np.clip(norm_xy[:, 1], 0.0, 1.0) * frame_h
    return np.array([xs.min(), ys.min(), xs.max(), ys.max()], dtype=np.float32)


def iou_xyxy(a: np.ndarray, b: np.ndarray) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    union = bbox_area_xyxy(a) + bbox_area_xyxy(b) - inter
    if union <= 1e-6:
        return 0.0
    return float(inter / union)


def mediapipe_result_to_candidates(result, frame_w: int, frame_h: int, min_visibility: float) -> List[Dict]:
    candidates = []
    if not getattr(result, "pose_landmarks", None):
        return candidates

    for pose_landmarks in result.pose_landmarks:
        pts33 = np.zeros((33, 3), dtype=np.float32)
        for j, lm in enumerate(pose_landmarks):
            score = float(getattr(lm, "visibility", 1.0))
            if score < min_visibility:
                score = 0.0
            pts33[j] = [float(lm.x), float(lm.y), score]

        pts17 = pts33[MP33_TO_COCO17].copy()
        bbox = compute_bbox_from_landmarks(pts17[:, :2], frame_w, frame_h)

        candidates.append(
            {
                "kpts": pts17,   # [17,3] => x,y,score
                "bbox": bbox,    # xyxy in pixels
            }
        )

    candidates.sort(key=lambda c: bbox_area_xyxy(c["bbox"]), reverse=True)
    return candidates


def assign_tracks(
    prev_boxes: List[Optional[np.ndarray]],
    candidates: List[Dict],
    max_persons: int,
) -> List[Optional[Dict]]:
    assigned: List[Optional[Dict]] = [None] * max_persons
    used = set()

    for pid in range(max_persons):
        prev_box = prev_boxes[pid]
        if prev_box is None:
            continue

        best_idx = -1
        best_iou = -1.0
        for i, cand in enumerate(candidates):
            if i in used:
                continue
            score = iou_xyxy(prev_box, cand["bbox"])
            if score > best_iou:
                best_iou = score
                best_idx = i

        if best_idx >= 0 and best_iou > 0.1:
            assigned[pid] = candidates[best_idx]
            used.add(best_idx)

    free_slots = [i for i in range(max_persons) if assigned[i] is None]
    remaining = [i for i in range(len(candidates)) if i not in used]

    for pid, cand_idx in zip(free_slots, remaining):
        assigned[pid] = candidates[cand_idx]

    return assigned


def sample_frame_indices(total_frames: int, target_frames: int) -> np.ndarray:
    if total_frames <= 0:
        return np.array([], dtype=np.int32)
    if total_frames == 1:
        return np.zeros((target_frames,), dtype=np.int32)
    idx = np.linspace(0, total_frames - 1, num=target_frames)
    return np.clip(np.round(idx).astype(np.int32), 0, total_frames - 1)


def read_selected_frames(video_path: Path, target_frames: int) -> Tuple[List[np.ndarray], float]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)

    if total_frames <= 0:
        buf = []
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            buf.append(frame)
        cap.release()
        if not buf:
            raise RuntimeError(f"No frames read from video: {video_path}")
        indices = sample_frame_indices(len(buf), target_frames)
        return [buf[i] for i in indices], fps

    indices = sample_frame_indices(total_frames, target_frames)
    frames: List[np.ndarray] = []

    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ok, frame = cap.read()
        if not ok or frame is None:
            if frames:
                frames.append(frames[-1].copy())
            else:
                raise RuntimeError(f"Failed to read first sampled frame at {idx} from {video_path}")
        else:
            frames.append(frame)

    cap.release()
    return frames, fps


def process_video(item: SampleItem, detector, output_root: Path, target_frames: int, max_persons: int, min_visibility: float, save_meta: bool):
    frames, fps = read_selected_frames(item.video_path, target_frames)
    if not frames:
        raise RuntimeError("No sampled frames")

    h, w = frames[0].shape[:2]
    T = target_frames
    V = 17
    M = max_persons
    C = 3  # x, y, score

    data = np.zeros((C, T, V, M), dtype=np.float32)
    prev_boxes: List[Optional[np.ndarray]] = [None] * M
    nonzero_frames = 0

    import mediapipe as mp

    for t, frame_bgr in enumerate(frames):
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        timestamp_ms = int((t / max(fps, 1.0)) * 1000.0)
        result = detector.detect_for_video(mp_image, timestamp_ms)

        candidates = mediapipe_result_to_candidates(result, w, h, min_visibility=min_visibility)
        assigned = assign_tracks(prev_boxes, candidates, M)

        any_person = False
        for pid, cand in enumerate(assigned):
            if cand is None:
                prev_boxes[pid] = None
                continue
            prev_boxes[pid] = cand["bbox"]
            kpts = cand["kpts"]  # [17,3]
            data[0, t, :, pid] = kpts[:, 0]
            data[1, t, :, pid] = kpts[:, 1]
            data[2, t, :, pid] = kpts[:, 2]
            if np.any(kpts[:, 2] > 0):
                any_person = True

        if any_person:
            nonzero_frames += 1

    split_out = output_root / item.split
    out_stem = split_out / item.rel_stem
    out_stem.parent.mkdir(parents=True, exist_ok=True)

    np.save(out_stem, data)

    meta = {
        "split": item.split,
        "class_name": item.class_name,
        "label": item.label,
        "video_path": str(item.video_path.resolve()),
        "rel_stem": item.rel_stem,
        "tensor_path": str((out_stem.with_suffix(".npy")).resolve()),
        "shape": list(data.shape),
        "frames_requested": target_frames,
        "frames_with_pose": int(nonzero_frames),
        "fps": fps,
        "width": w,
        "height": h,
    }

    if save_meta:
        with open(out_stem.with_suffix(".json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    return meta


def write_split_labels(splits_root: Path, split_name: str, rows: List[Dict]):
    splits_root.mkdir(parents=True, exist_ok=True)
    out_path = splits_root / f"{split_name}_labels.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


def main():
    args = parse_args()

    input_root = args.input_root.resolve()
    output_root = args.output_root.resolve()
    weights = args.weights.resolve()
    splits_root = output_root.parent / "splits"

    print(f"[INFO] cwd={Path.cwd()}", flush=True)
    print(f"[INFO] input_root={input_root}", flush=True)
    print(f"[INFO] output_root={output_root}", flush=True)
    print(f"[INFO] splits_root={splits_root}", flush=True)
    print(f"[INFO] weights={weights}", flush=True)

    if not input_root.exists():
        raise FileNotFoundError(f"Input root not found: {input_root}")
    if not weights.exists():
        raise FileNotFoundError(f"Weights file not found: {weights}")

    items = build_sample_list(input_root)
    if args.limit and args.limit > 0:
        items = items[: args.limit]

    print(f"[INFO] found_videos={len(items)}", flush=True)
    if not items:
        print("[WARN] No video files found. Check raw/train|val/Fight|NonFight structure.", flush=True)
        return

    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision

    base_options = python.BaseOptions(model_asset_path=str(weights))
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_poses=args.max_persons,
        min_pose_detection_confidence=0.3,
        min_pose_presence_confidence=0.3,
        min_tracking_confidence=0.3,
        output_segmentation_masks=False,
    )

    split_rows: Dict[str, List[Dict]] = {"train": [], "val": [], "test": []}
    failed: List[Dict] = []

    for i, item in enumerate(items, start=1):
        print(
            f"[{i}/{len(items)}] {item.split}/{item.class_name} -> {item.video_path.name}",
            flush=True,
        )
        try:
            with vision.PoseLandmarker.create_from_options(options) as detector:
                meta = process_video(
                    item=item,
                    detector=detector,
                    output_root=output_root,
                    target_frames=args.frames,
                    max_persons=args.max_persons,
                    min_visibility=args.min_visibility,
                    save_meta=args.save_meta,
                )
            split_rows[item.split].append(
                {
                    "sample_path": f"{item.split}/{item.rel_stem}.npy",
                    "rel_path": f"{item.split}/{item.rel_stem}.npy",
                    "rel_stem": item.rel_stem,
                    "label": item.label,
                    "class_name": item.class_name,
                    "video_path": str(item.video_path.resolve()),
                    "shape": meta["shape"],
                    "frames_with_pose": meta["frames_with_pose"],
                }
            )
        except Exception as e:
            tb = traceback.format_exc()
            print(f"[ERROR] {item.video_path}: {e}", flush=True)
            print(tb, flush=True)
            failed.append(
                {
                    "video_path": str(item.video_path.resolve()),
                    "split": item.split,
                    "class_name": item.class_name,
                    "error": str(e),
                    "traceback": tb,
                }
            )

    for split_name, rows in split_rows.items():
        if rows:
            write_split_labels(splits_root, split_name, rows)
            print(f"[INFO] wrote {split_name}_labels.json with {len(rows)} rows", flush=True)

    if failed:
        failed_path = output_root / "failed_files.json"
        with open(failed_path, "w", encoding="utf-8") as f:
            json.dump(failed, f, ensure_ascii=False, indent=2)
        print(f"[WARN] wrote failed file list: {failed_path}", flush=True)

    total_ok = sum(len(v) for v in split_rows.values())
    print(f"[DONE] success={total_ok}, failed={len(failed)}", flush=True)


if __name__ == "__main__":
    main()