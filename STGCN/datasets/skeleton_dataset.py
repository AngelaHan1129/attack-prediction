# datasets/skeleton_dataset.py
import os
import csv
import numpy as np
import torch
from torch.utils.data import Dataset

class SkeletonDataset(Dataset):
    def __init__(self, samples_dir, labels_csv, transform=None):
        self.samples_dir = samples_dir
        self.transform = transform
        self.items = []

        with open(labels_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.items.append({
                    "sample_id": row["sample_id"],
                    "label": int(row["label"])
                })

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        item = self.items[idx]
        sample_path = os.path.join(self.samples_dir, f"{item['sample_id']}.npy")
        data = np.load(sample_path).astype(np.float32)   # (C, T, V, M)
        label = item["label"]

        if self.transform is not None:
            data = self.transform(data)

        data = torch.tensor(data, dtype=torch.float32)
        label = torch.tensor(label, dtype=torch.long)

        return data, label