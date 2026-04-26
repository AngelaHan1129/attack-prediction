# scripts/preprocess.py
import os
import csv
import numpy as np

SEQ_LEN = 60
NUM_JOINTS = 33
NUM_CHANNELS = 3
NUM_PERSON = 1

LABEL_MAP = {
    "normal": 0,
    "suspicious": 1,
    "dangerous": 2
}

def normalize_keypoints(kpts, img_w, img_h):
    kpts = np.array(kpts, dtype=np.float32)  # (V, 4) or (V, 3)
    x = kpts[:, 0] / img_w
    y = kpts[:, 1] / img_h
    score = kpts[:, 3] if kpts.shape[1] >= 4 else np.ones(len(kpts), dtype=np.float32)
    out = np.stack([x, y, score], axis=0)    # (C, V)
    return out

def build_sequence(frame_keypoints, img_w, img_h):
    seq = []
    for kpts in frame_keypoints:
        if kpts is None:
            seq.append(np.zeros((NUM_CHANNELS, NUM_JOINTS), dtype=np.float32))
        else:
            seq.append(normalize_keypoints(kpts, img_w, img_h))

    seq = np.stack(seq, axis=1)  # (C, T, V)

    if seq.shape[1] < SEQ_LEN:
        pad = np.zeros((NUM_CHANNELS, SEQ_LEN - seq.shape[1], NUM_JOINTS), dtype=np.float32)
        seq = np.concatenate([seq, pad], axis=1)
    else:
        seq = seq[:, :SEQ_LEN, :]

    seq = np.expand_dims(seq, axis=-1)  # (C, T, V, M)
    return seq

def save_split(output_dir, sample_id, seq, label, csv_writer):
    os.makedirs(output_dir, exist_ok=True)
    np.save(os.path.join(output_dir, f"{sample_id}.npy"), seq)
    csv_writer.writerow([sample_id, LABEL_MAP[label]])

def main():
    os.makedirs("data/processed/train/samples", exist_ok=True)

    labels_path = "data/processed/train/labels.csv"
    with open(labels_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["sample_id", "label"])

        dummy_frames = [
            [[100, 200, 0.0, 0.95] for _ in range(NUM_JOINTS)]
            for _ in range(45)
        ]

        seq = build_sequence(dummy_frames, img_w=1920, img_h=1080)
        save_split("data/processed/train/samples", "clip_0001", seq, "dangerous", writer)

if __name__ == "__main__":
    main()