from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build packed ST-GCN dataset files from extracted per-video skeleton npy files"
    )
    parser.add_argument(
        "--processed-root",
        type=Path,
        default=Path("STGCN/data/processed"),
        help="Root directory containing per-video skeleton npy files",
    )
    parser.add_argument(
        "--splits-root",
        type=Path,
        default=Path("STGCN/data/splits"),
        help="Directory containing split label json/txt files",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("STGCN/data"),
        help="Output directory for packed ST-GCN files",
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        default=["train", "val", "test"],
        help="Splits to build, e.g. train val test",
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Skip missing split files or sample npy files instead of raising error",
    )
    parser.add_argument(
        "--dtype",
        type=str,
        default="float32",
        choices=["float32", "float16"],
        help="Packed dataset dtype",
    )
    parser.add_argument(
        "--save-stats",
        action="store_true",
        help="Also save dataset stats json for each split",
    )
    return parser.parse_args()


def load_split_rows(splits_root: Path, split: str) -> List[Dict]:
    json_path = splits_root / f"{split}_labels.json"
    txt_path = splits_root / f"{split}.txt"

    if json_path.exists():
        rows = json.loads(json_path.read_text(encoding="utf-8"))
        if not isinstance(rows, list):
            raise ValueError(f"Invalid JSON format in {json_path}")
        return rows

    if txt_path.exists():
        rows = []
        for line in txt_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            sample_path, label = line.rsplit(" ", 1)
            rows.append(
                {
                    "sample_path": sample_path,
                    "label": int(label),
                    "class_name": "unknown",
                    "video_path": "",
                }
            )
        return rows

    raise FileNotFoundError(f"No split file found for '{split}' in {splits_root}")


def normalize_sample_path(path_str: str) -> Path:
    return Path(path_str.replace("\\", "/"))


def infer_shape(rows: List[Dict], allow_missing: bool) -> Tuple[int, int, int, int]:
    for row in rows:
        sample_path_value = row.get("sample_path") or row.get("rel_path")
        if not sample_path_value:
            raise KeyError("sample_path")
        sample_path = normalize_sample_path(sample_path_value)
        if sample_path.exists():
            arr = np.load(sample_path)
            if arr.ndim != 4:
                raise ValueError(f"Expected 4D array (C,T,V,M), got {arr.shape} from {sample_path}")
            return tuple(arr.shape)
        if not allow_missing:
            raise FileNotFoundError(f"Sample file not found: {sample_path}")
    raise RuntimeError("Cannot infer sample shape because no valid sample files were found.")


def validate_and_collect(
    rows: List[Dict],
    expected_shape: Tuple[int, int, int, int],
    allow_missing: bool,
) -> Tuple[List[str], List[int], List[np.ndarray], List[Dict]]:
    sample_names: List[str] = []
    labels: List[int] = []
    data_list: List[np.ndarray] = []
    bad_rows: List[Dict] = []

    for row in rows:
        sample_path_value = row.get("sample_path") or row.get("rel_path")
        if not sample_path_value:
            raise KeyError("sample_path")
        sample_path = normalize_sample_path(sample_path_value)
        label = int(row["label"])

        if not sample_path.exists():
            msg = {"sample_path": str(sample_path), "reason": "missing_file"}
            if allow_missing:
                bad_rows.append(msg)
                continue
            raise FileNotFoundError(f"Sample file not found: {sample_path}")

        arr = np.load(sample_path)
        if arr.shape != expected_shape:
            msg = {
                "sample_path": str(sample_path),
                "reason": "shape_mismatch",
                "expected_shape": list(expected_shape),
                "actual_shape": list(arr.shape),
            }
            if allow_missing:
                bad_rows.append(msg)
                continue
            raise ValueError(
                f"Shape mismatch for {sample_path}: expected {expected_shape}, got {arr.shape}"
            )

        sample_names.append(sample_path.stem)
        labels.append(label)
        data_list.append(arr)
    return sample_names, labels, data_list, bad_rows


def pack_split(
    split: str,
    rows: List[Dict],
    output_root: Path,
    dtype: str,
    allow_missing: bool,
    save_stats: bool,
):
    expected_shape = infer_shape(rows, allow_missing=allow_missing)
    sample_names, labels, data_list, bad_rows = validate_and_collect(
        rows=rows,
        expected_shape=expected_shape,
        allow_missing=allow_missing,
    )

    if not data_list:
        raise RuntimeError(f"No valid samples found for split '{split}'")

    data = np.stack(data_list, axis=0).astype(dtype, copy=False)

    output_root.mkdir(parents=True, exist_ok=True)
    data_path = output_root / f"{split}_data.npy"
    label_path = output_root / f"{split}_label.pkl"

    np.save(data_path, data)

    with open(label_path, "wb") as f:
        pickle.dump((sample_names, labels), f)

    print(f"[{split}] data saved to: {data_path}")
    print(f"[{split}] label saved to: {label_path}")
    print(f"[{split}] shape: {data.shape}")

    if bad_rows:
        bad_path = output_root / f"{split}_skipped.json"
        bad_path.write_text(json.dumps(bad_rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[{split}] skipped samples saved to: {bad_path}")

    if save_stats:
        stats = build_stats(split, data, sample_names, labels, bad_rows, expected_shape)
        stats_path = output_root / f"{split}_stats.json"
        stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[{split}] stats saved to: {stats_path}")


def build_stats(
    split: str,
    data: np.ndarray,
    sample_names: List[str],
    labels: List[int],
    bad_rows: List[Dict],
    expected_shape: Tuple[int, int, int, int],
) -> Dict:
    unique, counts = np.unique(labels, return_counts=True)
    label_distribution = {int(k): int(v) for k, v in zip(unique.tolist(), counts.tolist())}

    score_channel_nonzero_ratio = None
    if data.shape[1] >= 3:
        score = data[:, 2]
        score_channel_nonzero_ratio = float(np.count_nonzero(score) / max(1, score.size))

    return {
        "split": split,
        "num_samples": int(len(sample_names)),
        "data_shape": list(data.shape),
        "per_sample_shape": list(expected_shape),
        "labels_distribution": label_distribution,
        "num_skipped": int(len(bad_rows)),
        "sample_name_examples": sample_names[:10],
        "score_channel_nonzero_ratio": score_channel_nonzero_ratio,
        "dtype": str(data.dtype),
    }


def main():
    args = parse_args()

    if not args.processed_root.exists():
        raise FileNotFoundError(f"Processed root not found: {args.processed_root}")
    if not args.splits_root.exists():
        raise FileNotFoundError(f"Splits root not found: {args.splits_root}")

    packed_root = args.output_root / "packed"
    packed_root.mkdir(parents=True, exist_ok=True)

    for split in args.splits:
        try:
            rows = load_split_rows(args.splits_root, split)
        except FileNotFoundError as e:
            if args.allow_missing:
                print(f"[SKIP] {e}")
                continue
            raise

        # If sample_path is relative, resolve from project root
        normalized_rows = []
        for row in rows:
            sample_path_value = row.get("sample_path") or row.get("rel_path")
            if not sample_path_value:
                raise KeyError("sample_path")
            sample_path = normalize_sample_path(sample_path_value)

            if not sample_path.is_absolute():
                sample_path = args.processed_root / sample_path

            normalized_rows.append(
                {
                    **row,
                    "sample_path": str(sample_path.resolve().as_posix()),
                }
            )

        pack_split(
            split=split,
            rows=normalized_rows,
            output_root=packed_root,
            dtype=args.dtype,
            allow_missing=args.allow_missing,
            save_stats=args.save_stats,
        )


if __name__ == "__main__":
    main()