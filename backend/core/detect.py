from ultralytics import YOLO
import cv2

model = YOLO("yolo26n.pt")

for i in range(5):
    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
    if cap.isOpened():
        print(f"鏡頭 {i} OK!")
        break
else:
    print("無鏡頭！用影片測試")
    cap = cv2.VideoCapture("test.mp4")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("讀取失敗")
        break

    results = model.track(
    frame,
    classes=[0],
    conf=0.5,
    persist=True,
    tracker="botsort.yaml"
)


    result = results[0]

    if result.boxes is not None and result.boxes.id is not None:
        boxes = result.boxes.xyxy.int().cpu().tolist()
        ids = result.boxes.id.int().cpu().tolist()
        confs = result.boxes.conf.cpu().tolist()

        for box, track_id, conf in zip(boxes, ids, confs):
            x1, y1, x2, y2 = box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                frame,
                f"person {track_id} {conf:.2f}",
                (x1, max(0, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

    cv2.imshow("YOLO ReID Tracking", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
