import cv2
import os
import time
from ultralytics import YOLO

# 用來控制任務停止的全域字典 (簡單實作)
# 在 yolo.py 中設定 stop_events[task_id] = True 即可停止
stop_events = {}

def run_detection(source="0", conf=0.5, save=False, task_id="default"):
    global stop_events
    stop_events[task_id] = False

    # 1. 載入模型
    model_path = os.path.join("weights", "yolo26n.pt")
    if not os.path.exists(model_path):
        print(f"❌ 找不到模型檔: {model_path}")
        return

    model = YOLO(model_path)

    # 2. 設定影像來源
    src = int(source) if source.isdigit() else source
    cap = cv2.VideoCapture(src, cv2.CAP_DSHOW) if isinstance(src, int) else cv2.VideoCapture(src)

    if not cap.isOpened():
        print(f"❌ 無法開啟來源: {src}")
        return

    # 確保輸出目錄存在
    snapshot_dir = os.path.join("data", "snapshots")
    os.makedirs(snapshot_dir, exist_ok=True)

    print(f"任務 {task_id} 開始執行...")

    try:
        while cap.isOpened():
            # 檢查外部停止訊號
            if stop_events.get(task_id):
                print(f"任務 {task_id} 接收到停止指令")
                break

            ret, frame = cap.read()
            if not ret:
                break

            # 執行追蹤
            results = model.track(
                frame,
                classes=[0],
                conf=conf,
                persist=True,
                tracker="botsort.yaml",
                verbose=False
            )

            # 繪製結果與邏輯處理
            if results[0].boxes is not None and results[0].boxes.id is not None:
                # 繪製 (這部分維持你原本的寫法)
                annotated_frame = results[0].plot() 
                
                # 每秒存一張截圖，供前端 API 調用顯示
                # 使用固定檔名 latest.jpg 讓前端容易讀取
                cv2.imwrite(os.path.join(snapshot_dir, f"{task_id}_latest.jpg"), annotated_frame)
            else:
                # 沒偵測到人也存一張原圖，保持畫面更新
                cv2.imwrite(os.path.join(snapshot_dir, f"{task_id}_latest.jpg"), frame)

            # 在背景任務中，waitKey(1) 仍可保留，但不要用 imshow
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except Exception as e:
        print(f"⚠️ 偵測過程中發生錯誤: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        stop_events.pop(task_id, None)
        print(f"任務 {task_id} 已安全結束")