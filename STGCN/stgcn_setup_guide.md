# ST-GCN 專案建置與執行指南

這份文件整理了 ST-GCN 專案從虛擬環境建立、資料夾結構、資料準備，到模型訓練與推論的最小可行流程，適用於目前以骨架時序資料做危險行為辨識的研究專案。[1]

## 專案目的

此專案的核心流程是將人員偵測與骨架抽取結果整理為時序骨架張量，再使用 ST-GCN 進行行為分類或風險分級。[1]
研究計畫中的技術路線包含 YOLO、MediaPipe Pose、ByteTrack、ST-GCN、LSTM 與 L0-L4 風險分級，因此專案結構應支援資料前處理、訓練、驗證與推論模組分離。[1]

## 建議資料夾結構

```text
project/
├─ data/
│  ├─ raw/
│  │  ├─ videos/
│  │  └─ annotations/
│  ├─ processed/
│  │  ├─ train/
│  │  │  ├─ samples/
│  │  │  └─ labels.csv
│  │  ├─ val/
│  │  │  ├─ samples/
│  │  │  └─ labels.csv
│  │  └─ test/
│  │     ├─ samples/
│  │     └─ labels.csv
│  └─ splits/
│     ├─ train.txt
│     ├─ val.txt
│     └─ test.txt
├─ models/
│  └─ stgcn.py
├─ datasets/
│  └─ skeleton_dataset.py
├─ scripts/
│  ├─ preprocess.py
│  ├─ train.py
│  └─ infer.py
├─ checkpoints/
├─ logs/
├─ config.py
└─ requirements.txt
```

這種結構能對應研究中 train/val/test 分流、骨架時序樣本管理與 ST-GCN 訓練流程，後續若加入 Re-ID、RAG 或 AHP 風險融合也容易擴充。[1]

## 虛擬環境建立

### Windows PowerShell

```powershell
cd project
python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Linux / macOS

```bash
cd project
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

虛擬環境可隔離 PyTorch、NumPy、OpenCV 與 scikit-learn 等套件版本，避免不同研究專案之間發生依賴衝突。[1]

## 建議 requirements.txt

```txt
numpy
pandas
scikit-learn
tqdm
matplotlib
opencv-python
torch
torchvision
torchaudio
```

這些套件足以支援骨架資料讀取、ST-GCN 訓練、基本評估與推論流程。[1]

## 資料格式規範

每一筆骨架樣本建議存成 `.npy` 檔案，shape 為 `(C, T, V, M)`。[1]
若以 MediaPipe Pose 為基礎，常見設定可為 `C=3`、`T=60`、`V=33`、`M=1`，也就是 `(3, 60, 33, 1)`。[1]

### 範例

```python
(3, 60, 33, 1)
```

各維度意義如下：

- `C`：特徵通道，例如 `x, y, score`
- `T`：時間長度，例如 60 幀
- `V`：關節數，例如 33 個關鍵點
- `M`：人物數，單人時通常為 1

這種格式與 ST-GCN 的標準骨架時序輸入形式一致，便於做空間與時間聯合建模。[1]

## labels.csv 格式

每個 split 都需要一份 `labels.csv`，至少包含 `sample_id` 與 `label` 兩欄。[1]

```csv
sample_id,label
clip_0001,2
clip_0002,0
clip_0003,1
```

如果 `labels.csv` 有資料，但對應的 `.npy` 不存在，Dataset 仍會視為無效樣本並跳過。[1]
因此 `sample_id` 必須與 `samples/clip_xxxx.npy` 的檔名完全一致。[1]

## 前處理流程

前處理的目的是把骨架結果整理為固定長度序列，再切分為 train、val、test 三組。[1]
研究計畫中提到可使用滑動視窗建立時序片段，並對應動作辨識與意圖預測任務，因此前處理是整體系統最重要的一步。[1]

### 前處理執行

```bash
python scripts/preprocess.py
```

完成後應至少產生：

- `data/processed/train/samples/*.npy`
- `data/processed/train/labels.csv`
- `data/processed/val/samples/*.npy`
- `data/processed/val/labels.csv`
- `data/processed/test/samples/*.npy`
- `data/processed/test/labels.csv`

如果 `val` 為空，`train.py` 會因為驗證資料集沒有有效樣本而報錯。[1]

## 訓練流程

訓練腳本會讀取 train 與 val split，建立 `SkeletonDataset` 與 `DataLoader`，再將資料送入 `SimpleSTGCN` 模型。[1]
模型最佳權重通常會存成 `checkpoints/best_stgcn.pth`，以便之後推論載入使用。[1]

### 訓練指令

```bash
python scripts/train.py
```

如果使用 CPU，終端機可能顯示：

```text
Using device: cpu
```

若環境有 CUDA 且 PyTorch 安裝正確，則可改以 GPU 訓練，這對 ST-GCN 之類的時序深度模型會更有效率。[1]

## 推論流程

推論腳本會讀取單一 `.npy` 樣本與訓練好的 checkpoint，輸出預測類別與機率。[1]
這個流程適合拿來驗證模型是否能正確分辨正常、可疑或危險行為，也可延伸到 L0-L4 風險分級任務。[1]

### 推論指令

```bash
python scripts/infer.py --sample data/processed/test/samples/clip_0001.npy
```

## 常見錯誤排查

### 找不到 `datasets` 模組

若出現 `ModuleNotFoundError: No module named 'datasets'`，通常代表 `train.py` 或 `infer.py` 沒有把專案根目錄加入 `sys.path`。[1]
這種情況可在腳本最前面加入 root path 修正，或建立 `datasets/__init__.py`、`models/__init__.py`、`scripts/__init__.py` 讓 Python 更穩定地辨識 package。[1]

### 驗證資料集為空

若出現 `No valid samples found in ... val ... labels.csv`，代表 `val/samples` 沒有對應 `.npy`，或 `val/labels.csv` 為空、格式錯誤。[1]
最小可跑測試可先把一筆 train 樣本複製到 val 與 test，但正式研究仍應使用獨立驗證集與測試集。[1]

### shape 錯誤

若 `.npy` shape 不是 `(C, T, V, M)`，模型會在 Dataset 或 forward 階段報錯。[1]
可用以下指令檢查：

```bash
python -c "import numpy as np; x=np.load('data/processed/train/samples/clip_0001.npy'); print(x.shape)"
```

若輸出為 `(3, 60, 33, 1)`，則與目前模型版本相容。[1]

## 建議的最小可行流程

```bash
cd project
python -m venv venv
# Windows: venv\Scripts\Activate.ps1
# Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
python scripts/preprocess.py
python scripts/train.py
python scripts/infer.py --sample data/processed/test/samples/clip_0001.npy
```