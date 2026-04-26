# scripts/train.py
import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from datasets.skeleton_dataset import SkeletonDataset
from models.stgcn import SimpleSTGCN

def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss, total_correct, total = 0.0, 0, 0

    for x, y in loader:
        x, y = x.to(device), y.to(device)

        optimizer.zero_grad()
        out = model(x)
        loss = criterion(out, y)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * x.size(0)
        pred = out.argmax(dim=1)
        total_correct += (pred == y).sum().item()
        total += y.size(0)

    return total_loss / total, total_correct / total

def validate(model, loader, criterion, device):
    model.eval()
    total_loss, total_correct, total = 0.0, 0, 0

    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            out = model(x)
            loss = criterion(out, y)

            total_loss += loss.item() * x.size(0)
            pred = out.argmax(dim=1)
            total_correct += (pred == y).sum().item()
            total += y.size(0)

    return total_loss / total, total_correct / total

def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"

    train_dataset = SkeletonDataset(
        samples_dir="data/processed/train/samples",
        labels_csv="data/processed/train/labels.csv"
    )
    val_dataset = SkeletonDataset(
        samples_dir="data/processed/val/samples",
        labels_csv="data/processed/val/labels.csv"
    )

    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=16, shuffle=False, num_workers=2)

    model = SimpleSTGCN(in_channels=3, num_class=3, num_point=33, num_person=1).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)

    best_val_acc = 0.0
    os.makedirs("checkpoints", exist_ok=True)

    for epoch in range(1, 31):
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = validate(model, val_loader, criterion, device)

        print(f"Epoch {epoch:03d} | "
              f"Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | "
              f"Val Loss: {val_loss:.4f} Acc: {val_acc:.4f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), "checkpoints/best_stgcn.pth")

    print("Best Val Acc:", best_val_acc)

if __name__ == "__main__":
    main()