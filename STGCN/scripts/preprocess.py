import csv
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

RAW_ROOT = Path(r"C:\Users\User\Desktop\nutc\YS_LAB\研究\attack-prediction\STGCN\data\raw\rwf2000")
OUT_ROOT = Path(r"C:\Users\User\Desktop\nutc\YS_LAB\研究\attack-prediction\STGCN\data\processed")
TARGET_T = 60
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".m4v"}
MODEL_PATH = Path(r"C:\mp_models\pose_landmarker_lite.task")

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode


def iter_videos(root: Path):
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix.lower() in VIDEO_EXTS:
            yield p


def extract_pose_sequence(video_path: Path, target_t: int = TARGET_T):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"[SKIP] cannot open: {video_path}")
        return None

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Missing model file: {MODEL_PATH}")

    frames = []
    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODEL_PATH)),
        running_mode=VisionRunningMode.VIDEO,
        num_poses=1,
        output_segmentation_masks=False,
    )

    with PoseLandmarker.create_from_options(options) as landmarker:
        idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            timestamp_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))

            result = landmarker.detect_for_video(mp_image, timestamp_ms)

            if result.pose_landmarks and len(result.pose_landmarks) > 0:
                landmarks = result.pose_landmarks[0]
                pts = np.array(
                    [[lm.x, lm.y, lm.visibility] for lm in landmarks],
                    dtype=np.float32,
                )
            else:
                pts = np.zeros((33, 3), dtype=np.float32)

            frames.append(pts)
            idx += 1

    cap.release()

    if len(frames) == 0:
        return None

    seq = np.stack(frames, axis=0)

    if seq.shape[0] >= target_t:
        seq = seq[:target_t]
    else:
        pad = np.zeros((target_t - seq.shape[0], 33, 3), dtype=np.float32)
        seq = np.concatenate([seq, pad], axis=0)

    seq = np.transpose(seq, (2, 0, 1))
    seq = np.expand_dims(seq, axis=-1)
    return seq


def process_split(split_name: str):
    split_dir = RAW_ROOT / split_name
    out_split_dir = OUT_ROOT / split_name
    out_samples = out_split_dir / "samples"
    out_samples.mkdir(parents=True, exist_ok=True)

    rows = []
    count = 0

    for video_path in iter_videos(split_dir):
        cls = video_path.parent.name
        label = 1 if cls.lower() == "fight" else 0
        sample_id = video_path.stem

        print(f"[{split_name}] {video_path.relative_to(RAW_ROOT)}")
        seq = extract_pose_sequence(video_path)
        if seq is None:
            print("  -> skip")
            continue

        np.save(out_samples / f"{sample_id}.npy", seq)
        rows.append(
            {
                "sample_id": sample_id,
                "label": label,
                "class_name": cls,
                "video_path": str(video_path),
            }
        )
        count += 1

    csv_path = out_split_dir / "labels.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["sample_id", "label", "class_name", "video_path"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"[DONE] {split_name}: {count} samples -> {csv_path}")


def main():
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    for split in ["train", "val"]:
        process_split(split)


if __name__ == "__main__":
    main()