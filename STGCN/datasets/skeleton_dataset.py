# datasets/skeleton_dataset.py
import os
import csv
import numpy as np
import torch
from torch.utils.data import Dataset


class SkeletonDataset(Dataset):
    def __init__(self, samples_dir, labels_csv, transform=None):
        self.samples_dir = samples_dir
        self.labels_csv = labels_csv
        self.transform = transform
        self.items = []

        if not os.path.exists(samples_dir):
            raise FileNotFoundError(f"Samples directory not found: {samples_dir}")

        if not os.path.exists(labels_csv):
            raise FileNotFoundError(f"Labels file not found: {labels_csv}")

        with open(labels_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sample_id = row["sample_id"].strip()
                label = int(row["label"])
                sample_path = os.path.join(samples_dir, f"{sample_id}.npy")

                if os.path.exists(sample_path):
                    self.items.append({
                        "sample_id": sample_id,
                        "label": label,
                        "sample_path": sample_path
                    })
                else:
                    print(f"[Warning] Sample file not found, skipped: {sample_path}")

        if len(self.items) == 0:
            raise ValueError(f"No valid samples found in {samples_dir} with {labels_csv}")

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        item = self.items[idx]
        data = np.load(item["sample_path"]).astype(np.float32)  # expected: (C, T, V, M)

        if data.ndim != 4:
            raise ValueError(
                f"Sample {item['sample_id']} shape must be 4D (C, T, V, M), got {data.shape}"
            )

        if self.transform is not None:
            data = self.transform(data)

        data = torch.tensor(data, dtype=torch.float32)
        label = torch.tensor(item["label"], dtype=torch.long)

        return data, label