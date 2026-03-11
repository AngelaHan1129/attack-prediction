cap = cv2.VideoCapture(0)  # webcam
# 同上迴圈，替換 source 即可
results = model(frame, classes=0, persist=True, tracker="bytetrack.yaml")  # 加 ByteTrack 追蹤 ID，接你的計畫
