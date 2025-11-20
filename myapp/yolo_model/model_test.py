from ultralytics import YOLO

model = YOLO("weights.pt")

import cv2

cap = cv2.VideoCapture(0)

while True :
    ret, frame = cap.read()
    if not ret : break

    results = model(frame, conf=0.25, verbose=False)

    for result in results :
        for box in result.boxes :
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            label = f"{model.names[cls_id]} {conf:.2f}"

            # dessiner le rectangle et le texte
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 255, 0), 2)

    cv2.imshow("YOLO Webcam", frame)

    if cv2.waitKey(1) & 0xFF == ord('q') : break

cap.release()
cv2.destroyAllWindows()
