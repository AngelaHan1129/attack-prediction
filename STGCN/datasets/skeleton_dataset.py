import os
import pickle
import numpy as np
import torch
from torch.utils.data import Dataset


class SkeletonDataset(Dataset):
    def __init__(self, data_path, label_path, transform=None, mmap_mode="r"):
        self.data_path = data_path
        self.label_path = label_path
        self.transform = transform

        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Data file not found: {data_path}")

        if not os.path.exists(label_path):
            raise FileNotFoundError(f"Label file not found: {label_path}")

        self.data = np.load(data_path, mmap_mode=mmap_mode)

        with open(label_path, "rb") as f:
            obj = pickle.load(f)

        if not isinstance(obj, (list, tuple)) or len(obj) != 2:
            raise ValueError(f"Label file format invalid: {label_path}")

        self.sample_names, self.labels = obj

        if len(self.data) != len(self.labels):
            raise ValueError(
                f"Data/label length mismatch: data={len(self.data)}, labels={len(self.labels)}"
            )

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        data = self.data[idx].astype(np.float32)
        label = int(self.labels[idx])

        if data.ndim != 4:
            raise ValueError(f"Sample index {idx} shape must be 4D (C,T,V,M), got {data.shape}")

        if self.transform is not None:
            data = self.transform(data)

        data = torch.tensor(data, dtype=torch.float32)
        label = torch.tensor(label, dtype=torch.long)
        return data, label
