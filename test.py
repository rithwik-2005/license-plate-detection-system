import cv2
from ultralytics import YOLO
import cvzone
from paddleocr import PaddleOCR
from datetime import datetime
import pandas as pd

# Load YOLO and PaddleOCR
model = YOLO('best.pt')  # Replace with your trained model
names = model.names

ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False
)

# Prepare Excel file
now_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
log_filename = f"plates_{now_str}.xlsx"

saved_ids = set()
id_to_plate = {}
log_data = []  # Store entries before writing to Excel

# Mouse debugging (optional)
def RGB(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:
        print(f"Mouse moved to: [{x}, {y}]")

cv2.namedWindow("RGB")
cv2.setMouseCallback("RGB", RGB)

# Load video
cap = cv2.VideoCapture("vid1.mp4")
frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    if frame_count % 3 != 0:
        continue

    frame = cv2.resize(frame, (1020, 600))
    results = model.track(frame, persist=True)

    if results[0].boxes.id is not None:
        ids = results[0].boxes.id.cpu().numpy().astype(int)
        boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)
        class_ids = results[0].boxes.cls.int().cpu().tolist()

        for track_id, box, class_id in zip(ids, boxes, class_ids):
            x1, y1, x2, y2 = box
            label = names[class_id]

            # Draw bounding box and label
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cvzone.putTextRect(frame, f'{label.upper()}', (x1, y1 - 10), scale=1, thickness=2,
                               colorT=(255, 255, 255), colorR=(0, 0, 255), offset=5, border=2)

            # Detect and recognize number plate text
            if label.lower() == "numberplate":
                cropped_plate = frame[y1:y2, x1:x2]
                if cropped_plate.size == 0:
                    continue

                if track_id not in id_to_plate:
                    result = ocr.predict(cropped_plate)
                    plate_text = ""

                    # Extract detected text
                    if result and isinstance(result, list) and "rec_texts" in result[0]:
                        rec_texts = result[0]["rec_texts"]
                        plate_text = " ".join(rec_texts)
                        print(f"Full Plate: {plate_text}")

                    if plate_text:
                        id_to_plate[track_id] = plate_text
                        if track_id not in saved_ids:
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            log_data.append({"Timestamp": timestamp, "ID": track_id, "Plate": plate_text})

                            # Write data to Excel
                            df = pd.DataFrame(log_data)
                            df.to_excel(log_filename, index=False)

                            saved_ids.add(track_id)
                            print(f"Saved to Excel: ID={track_id}, Plate={plate_text}")

                # Display detected plate text on video
                if track_id in id_to_plate:
                    plate_text = id_to_plate[track_id]
                    label_text = f"ID: {track_id} | {plate_text}"
                    cvzone.putTextRect(frame, label_text, (x1, y2 + 10), scale=1, thickness=2,
                                       colorT=(0, 0, 0), colorR=(255, 255, 0), offset=5, border=2)
                else:
                    cvzone.putTextRect(frame, f"ID: {track_id}", (x1, y2 + 10), scale=1, thickness=2,
                                       colorT=(255, 255, 255), colorR=(0, 255, 0), offset=5, border=2)

    cv2.imshow("RGB", frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC key to exit
        break

cap.release()
cv2.destroyAllWindows()
