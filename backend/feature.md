如果你目前系統只做到「可以抓到人」，那下一步不要急著做攻擊預測，應該先把「抓到的人」變成「可持續追蹤、可累積序列、可輸出特徵」的人。依你的研究設計，正確順序應該是：人偵測 → 多目標追蹤/跨鏡關聯 → 骨架提取 → 滑動視窗 → 風險特徵 → 意圖預測，而不是一抓到人就直接跳 ST-GCN/LSTM。 [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71319359/f7732331-7944-4bc6-a065-d85b1e8ca459/paste-2.txt)

## 第一個下一步

你現在最先要補的是 **追蹤**，不是訓練。因為只會框出人還不夠，你後面所有時序分析都依賴「同一個人能在連續幀內維持同一個 ID」，而你的研究方法本來就把 ByteTrack 當成目標鎖定的核心，目的是在擁擠與遮擋場景維持追蹤連貫性。 [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71319359/58096a76-9436-44d7-be31-86230255e060/C802-Yan-Jiu-Ji-Hua-Zhai-Yao-Biao-Yun-Yong-Wu-Jian-Zhen-Ce-Yu-Duo-Tong-Dao-Shi-Xu-Fen-Xi-Jin-Xing-Gong-Ji-Yi-Tu-Yu-Ce-Zhi-Yan-Jiu-final.docx)
所以你下一步應先做到：每個人都有穩定 `track_id`，而且在畫面中移動、短暫遮擋後不要立刻換 ID；如果這一步不穩，後面的骨架序列與風險分數都會全亂掉。 [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71319359/58096a76-9436-44d7-be31-86230255e060/C802-Yan-Jiu-Ji-Hua-Zhai-Yao-Biao-Yun-Yong-Wu-Jian-Zhen-Ce-Yu-Duo-Tong-Dao-Shi-Xu-Fen-Xi-Jin-Xing-Gong-Ji-Yi-Tu-Yu-Ce-Zhi-Yan-Jiu-final.docx)

## 第二個下一步

追蹤穩了之後，馬上接 **骨架提取**。因為你的攻擊預測核心不是 bbox，而是人體姿態與動作演變；你的計畫書也明確指定 MediaPipe Pose 提取 33 個 3D 關鍵點，再交給 ST-GCN 與 LSTM 做時序分析。 [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71319359/58096a76-9436-44d7-be31-86230255e060/C802-Yan-Jiu-Ji-Hua-Zhai-Yao-Biao-Yun-Yong-Wu-Jian-Zhen-Ce-Yu-Duo-Tong-Dao-Shi-Xu-Fen-Xi-Jin-Xing-Gong-Ji-Yi-Tu-Yu-Ce-Zhi-Yan-Jiu-final.docx)
所以你現在應該先完成：對每個被追蹤到的人框，裁切人物區域，穩定輸出 33 點骨架，並確認每幀都能把骨架與 `track_id/person_id/timestamp/camera_id` 綁在一起。 [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71319359/f7732331-7944-4bc6-a065-d85b1e8ca459/paste-2.txt)

## 第三個下一步

當你能穩定抓到「同一個人」的骨架後，就要開始 **存資料**，不要只顯示在畫面上。你前面的程式已經有 `skeleton_sequence` 概念，但從整理內容看，真正缺的是把這些資料變成可訓練的樣本。 [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71319359/f7732331-7944-4bc6-a065-d85b1e8ca459/paste-2.txt)
所以現在最實際的任務是：每一幀把 `person_id / track_id / bbox / timestamp / camera_id / keypoints` 存成 `meta.json` 或 JSONL，之後才能切出 150 幀或 300 幀的 sliding window，供 ST-GCN/LSTM 訓練與驗證。 [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71319359/f7732331-7944-4bc6-a065-d85b1e8ca459/paste-2.txt)

## 第四個下一步

資料能存之後，不要先訓練，先做 **sliding window**。你的研究方法已經明確設定用 5–10 秒視窗，也就是約 150–300 幀的骨架序列來建模攻擊前兆與時序演化。 [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71319359/58096a76-9436-44d7-be31-86230255e060/C802-Yan-Jiu-Ji-Hua-Zhai-Yao-Biao-Yun-Yong-Wu-Jian-Zhen-Ce-Yu-Duo-Tong-Dao-Shi-Xu-Fen-Xi-Jin-Xing-Gong-Ji-Yi-Tu-Yu-Ce-Zhi-Yan-Jiu-final.docx)
所以你現在應做的是：把同一個 `person_id` 的連續骨架切成固定長度窗口，並保留開始時間、結束時間、鏡頭路徑與是否有效。這一步做好，後面規則引擎、標註與模型訓練才有共同輸入單位。 [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71319359/f7732331-7944-4bc6-a065-d85b1e8ca459/paste-2.txt)

## 第五個下一步

有了 window 之後，先做 **規則版風險特徵**，不要直接上深度模型。因為你的論文裡已經定義了 9 個攻擊意圖指數 X1–X9，例如武器準備、拳擊姿態、追逐衝刺、徘徊、尾隨、距離侵略、群聚對峙、歷史風險與空間脈絡，這些完全可以先做成 heuristic baseline。 [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71319359/58096a76-9436-44d7-be31-86230255e060/C802-Yan-Jiu-Ji-Hua-Zhai-Yao-Biao-Yun-Yong-Wu-Jian-Zhen-Ce-Yu-Duo-Tong-Dao-Shi-Xu-Fen-Xi-Jin-Xing-Gong-Ji-Yi-Tu-Yu-Ce-Zhi-Yan-Jiu-final.docx)
換句話說，你下一步最值得做的是：從骨架與軌跡算出手肘角度、移動速度、路徑熵、跟隨時間、最近距離等特徵，先用 AHP 算出 L0–L4。這樣你會先有一版可跑、可看、可 debug 的攻擊預測雛形。 [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71319359/f7732331-7944-4bc6-a065-d85b1e8ca459/paste-2.txt)

## 目前最合理的順序

以你現在「只抓得到人」的狀態，最合理的開發順序是：

- 人物偵測穩定化：先把 person detection precision/recall 與 FPS 調到可接受。 [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71319359/58096a76-9436-44d7-be31-86230255e060/C802-Yan-Jiu-Ji-Hua-Zhai-Yao-Biao-Yun-Yong-Wu-Jian-Zhen-Ce-Yu-Duo-Tong-Dao-Shi-Xu-Fen-Xi-Jin-Xing-Gong-Ji-Yi-Tu-Yu-Ce-Zhi-Yan-Jiu-final.docx)
- ByteTrack：讓每個人有連續 `track_id`。 [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71319359/58096a76-9436-44d7-be31-86230255e060/C802-Yan-Jiu-Ji-Hua-Zhai-Yao-Biao-Yun-Yong-Wu-Jian-Zhen-Ce-Yu-Duo-Tong-Dao-Shi-Xu-Fen-Xi-Jin-Xing-Gong-Ji-Yi-Tu-Yu-Ce-Zhi-Yan-Jiu-final.docx)
- MediaPipe Pose：對每個 track 提取 33 點骨架。 [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71319359/58096a76-9436-44d7-be31-86230255e060/C802-Yan-Jiu-Ji-Hua-Zhai-Yao-Biao-Yun-Yong-Wu-Jian-Zhen-Ce-Yu-Duo-Tong-Dao-Shi-Xu-Fen-Xi-Jin-Xing-Gong-Ji-Yi-Tu-Yu-Ce-Zhi-Yan-Jiu-final.docx)
- 資料落盤：把每幀追蹤與骨架資料存下來。 [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71319359/f7732331-7944-4bc6-a065-d85b1e8ca459/paste-2.txt)
- Sliding window：切成 150/300 幀窗口。 [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71319359/58096a76-9436-44d7-be31-86230255e060/C802-Yan-Jiu-Ji-Hua-Zhai-Yao-Biao-Yun-Yong-Wu-Jian-Zhen-Ce-Yu-Duo-Tong-Dao-Shi-Xu-Fen-Xi-Jin-Xing-Gong-Ji-Yi-Tu-Yu-Ce-Zhi-Yan-Jiu-final.docx)
- X1–X9 特徵：先做可解釋風險指數。 [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71319359/58096a76-9436-44d7-be31-86230255e060/C802-Yan-Jiu-Ji-Hua-Zhai-Yao-Biao-Yun-Yong-Wu-Jian-Zhen-Ce-Yu-Duo-Tong-Dao-Shi-Xu-Fen-Xi-Jin-Xing-Gong-Ji-Yi-Tu-Yu-Ce-Zhi-Yan-Jiu-final.docx)
- AHP baseline：先輸出 L0–L4。 [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71319359/58096a76-9436-44d7-be31-86230255e060/C802-Yan-Jiu-Ji-Hua-Zhai-Yao-Biao-Yun-Yong-Wu-Jian-Zhen-Ce-Yu-Duo-Tong-Dao-Shi-Xu-Fen-Xi-Jin-Xing-Gong-Ji-Yi-Tu-Yu-Ce-Zhi-Yan-Jiu-final.docx)
- 標註資料：定義 action / risk 標籤。 [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71319359/58096a76-9436-44d7-be31-86230255e060/C802-Yan-Jiu-Ji-Hua-Zhai-Yao-Biao-Yun-Yong-Wu-Jian-Zhen-Ce-Yu-Duo-Tong-Dao-Shi-Xu-Fen-Xi-Jin-Xing-Gong-Ji-Yi-Tu-Yu-Ce-Zhi-Yan-Jiu-final.docx)
- ST-GCN baseline：先做行為分類。 [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71319359/58096a76-9436-44d7-be31-86230255e060/C802-Yan-Jiu-Ji-Hua-Zhai-Yao-Biao-Yun-Yong-Wu-Jian-Zhen-Ce-Yu-Duo-Tong-Dao-Shi-Xu-Fen-Xi-Jin-Xing-Gong-Ji-Yi-Tu-Yu-Ce-Zhi-Yan-Jiu-final.docx)
- LSTM：再做 next-risk 預測。 [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71319359/58096a76-9436-44d7-be31-86230255e060/C802-Yan-Jiu-Ji-Hua-Zhai-Yao-Biao-Yun-Yong-Wu-Jian-Zhen-Ce-Yu-Duo-Tong-Dao-Shi-Xu-Fen-Xi-Jin-Xing-Gong-Ji-Yi-Tu-Yu-Ce-Zhi-Yan-Jiu-final.docx)

## 你今天就能做的事

如果你想要最具體的版本，那你今天就先完成這 3 件事：

- 在每個 detection 上接 ByteTrack，讓畫面中每個人都有穩定 `track_id`。 [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71319359/58096a76-9436-44d7-be31-86230255e060/C802-Yan-Jiu-Ji-Hua-Zhai-Yao-Biao-Yun-Yong-Wu-Jian-Zhen-Ce-Yu-Duo-Tong-Dao-Shi-Xu-Fen-Xi-Jin-Xing-Gong-Ji-Yi-Tu-Yu-Ce-Zhi-Yan-Jiu-final.docx)
- 對每個 `track_id` 的 crop 跑 MediaPipe Pose，確認你能拿到 33 個關鍵點。 [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71319359/58096a76-9436-44d7-be31-86230255e060/C802-Yan-Jiu-Ji-Hua-Zhai-Yao-Biao-Yun-Yong-Wu-Jian-Zhen-Ce-Yu-Duo-Tong-Dao-Shi-Xu-Fen-Xi-Jin-Xing-Gong-Ji-Yi-Tu-Yu-Ce-Zhi-Yan-Jiu-final.docx)
- 把 `timestamp, camera_id, track_id, bbox, keypoints` 存成檔案，不要只在記憶體裡跑完。 [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71319359/f7732331-7944-4bc6-a065-d85b1e8ca459/paste-2.txt)

## 一句話版本

你現在的下一步不是「做攻擊預測模型」，而是先把系統升級成「可追蹤同一個人、可累積骨架序列、可切窗保存資料」的版本；沒有這一步，後面 ST-GCN、LSTM、AHP、RAG 都接不起來。 [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71319359/f7732331-7944-4bc6-a065-d85b1e8ca459/paste-2.txt)

如果你要，我下一則可以直接照你現在「只抓到人」的狀態，幫你排一份 **7 天開發清單**，每天要做什麼、改哪些模組、驗收什麼。

# Attack Intent System Starter

## Project Tree

```text
attack-intent-system/
├─ apps/
│  ├─ backend/
│  │  ├─ api/
│  │  │  ├─ routes/
│  │  │  │  ├─ streams.py
│  │  │  │  ├─ inference.py
│  │  │  │  ├─ alerts.py
│  │  │  │  ├─ events.py
│  │  │  │  └─ search.py
│  │  │  └─ schemas/
│  │  ├─ services/
│  │  │  ├─ feature_engine/
│  │  │  ├─ intent_model/
│  │  │  ├─ risk_engine/
│  │  │  └─ rag/
│  │  ├─ workers/
│  │  └─ core/
│  ├─ dashboard/
│  └─ annotator/
├─ data/
│  ├─ raw/
│  ├─ interim/
│  │  ├─ tracks/
│  │  ├─ poses/
│  │  └─ windows/
│  └─ processed/
│     ├─ train/
│     ├─ val/
│     └─ test/
├─ models/
├─ scripts/
├─ configs/
├─ storage/
├─ tests/
└─ docs/
```

## meta.json example

```json
{
  "frame_id": 1832,
  "timestamp": "2026-04-05T13:10:21.233+08:00",
  "camera_id": "cam_01",
  "track_id": 17,
  "person_id": 5,
  "bbox_xyxy": [422, 138, 560, 442],
  "det_conf": 0.93,
  "reid_score": 0.81,
  "is_cross_camera": false,
  "pose_file": "data/interim/poses/cam_01/0001832_p5.npy"
}
```

## window.json example

```json
{
  "window_id": "cam01_p5_20260405_131020_131025",
  "person_id": 5,
  "start_ts": "2026-04-05T13:10:20+08:00",
  "end_ts": "2026-04-05T13:10:25+08:00",
  "frames": 150,
  "camera_path": ["cam_01", "cam_01", "cam_02"],
  "pose_seq_file": "data/interim/windows/cam01_p5_20260405_131020_131025/pose.npy",
  "feature_seq_file": "data/interim/windows/cam01_p5_20260405_131020_131025/features.json",
  "label_action": "loitering_to_intrusion",
  "label_risk": "L2",
  "label_next_risk": "L3"
}
```

## FastAPI routes

- `POST /api/streams/register`
- `GET /api/streams`
- `POST /api/streams/{stream_id}/start`
- `POST /api/streams/{stream_id}/stop`
- `GET /api/inference/live`
- `GET /api/inference/person/{person_id}`
- `GET /api/inference/window/{window_id}`
- `GET /api/alerts`
- `GET /api/alerts/{event_id}`
- `POST /api/alerts/{event_id}/ack`
- `POST /api/alerts/{event_id}/resolve`
- `GET /api/events/{event_id}/clip`
- `GET /api/events/{event_id}/timeline`
- `POST /api/search/similar-events`
- `POST /api/search/text`
- `GET /api/models/status`
- `POST /api/models/reload`
- `GET /api/metrics/system`