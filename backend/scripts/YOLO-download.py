from ultralytics import YOLO

model = YOLO("yolo26n.pt")  # 下載 nano 模型；可用 yolo26s.pt 等
# 或 pose 版：YOLO("yolo26n-pose.pt")  # 內建 keypoints，適合你的 MediaPipe 接續
