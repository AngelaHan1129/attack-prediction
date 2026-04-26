# scripts/infer.py
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

import argparse
import numpy as np
import torch
import torch.nn.functional as F

from models.stgcn import SimpleSTGCN


LABEL_MAP = {
    0: "normal",
    1: "suspicious",
    2: "dangerous"
}


def load_model(model_path, device):
    model = SimpleSTGCN(
        in_channels=3,
        num_class=3,
        num_point=33,
        num_person=1
    ).to(device)

    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    return model


def infer_single_sample(model, sample_path, device):
    if not os.path.exists(sample_path):
        raise FileNotFoundError(f"Sample not found: {sample_path}")

    data = np.load(sample_path).astype(np.float32)  # (C, T, V, M)

    if data.ndim != 4:
        raise ValueError(f"Input sample shape must be (C, T, V, M), got {data.shape}")

    x = torch.tensor(data, dtype=torch.float32).unsqueeze(0).to(device)  # (1, C, T, V, M)

    with torch.no_grad():
        outputs = model(x)
        probs = F.softmax(outputs, dim=1)
        pred_idx = torch.argmax(probs, dim=1).item()
        confidence = probs[0, pred_idx].item()

    return pred_idx, confidence, probs.cpu().numpy()[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sample",
        type=str,
        default=os.path.join(ROOT_DIR, "data", "processed", "test", "samples", "clip_0001.npy"),
        help="Path to a .npy sample"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.path.join(ROOT_DIR, "checkpoints", "best_stgcn.pth"),
        help="Path to model checkpoint"
    )
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    model = load_model(args.model, device)
    pred_idx, confidence, probs = infer_single_sample(model, args.sample, device)

    print(f"Sample: {args.sample}")
    print(f"Predicted class: {pred_idx} ({LABEL_MAP[pred_idx]})")
    print(f"Confidence: {confidence:.4f}")
    print("Class probabilities:")
    for i, p in enumerate(probs):
        print(f"  {i} ({LABEL_MAP[i]}): {p:.4f}")


if __name__ == "__main__":
    main()