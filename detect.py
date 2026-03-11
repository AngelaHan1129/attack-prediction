from ultralytics import YOLO
import cv2
import numpy as np  # 加這行

model = YOLO("yolo26n.pt")

# 修復 Windows 鏡頭
for i in range(5):  # 試 0-4 index
    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
    if cap.isOpened():
        print(f"鏡頭 {i} OK!")
        break
else:
    print("無鏡頭！用影片測試")
    cap = cv2.VideoCapture("test.mp4")  # 下載測試影片

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: 
        print("讀取失敗")
        break
    results = model(frame, classes=0, conf=0.5)
    annotated = results[0].plot()
    cv2.imshow("YOLO Detection", annotated)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()
