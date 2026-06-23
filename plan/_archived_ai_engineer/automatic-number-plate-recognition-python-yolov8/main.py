import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path

import util
from sort.sort import *
from util import get_car, read_license_plate, write_csv

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "yolov8n.pt"
PLATE_MODEL_PATHS = [
    BASE_DIR / "license_plate_detector.pt",
]
VIDEO_PATHS = [
    BASE_DIR / "uploads" / "2103099-uhd_3840_2160_30fps.mp4",
]

PLATE_MODEL_PATH = next(
    (p for p in PLATE_MODEL_PATHS if p.exists()), PLATE_MODEL_PATHS[0]
)
VIDEO_PATH = next((p for p in VIDEO_PATHS if p.exists()), VIDEO_PATHS[0])

missing = [p for p in [MODEL_PATH, PLATE_MODEL_PATH, VIDEO_PATH] if not p.exists()]
if missing:
    missing_names = ", ".join(str(p) for p in missing)
    raise FileNotFoundError(
        f"Missing required file(s): {missing_names}.\n"
        f"Place them in {BASE_DIR} or update the paths in main.py."
    )

results = {}

mot_tracker = Sort()

# load models
coco_model = YOLO(str(MODEL_PATH))
license_plate_detector = YOLO(str(PLATE_MODEL_PATH))

# load video
cap = cv2.VideoCapture(str(VIDEO_PATH))

vehicles = [2, 3, 5, 7]

# read frames
best_license_plates = {}
frame_nmr = -1
ret = True
while ret:
    frame_nmr += 1
    ret, frame = cap.read()
    if ret:
        # Resize frame to 1280x720 for faster CPU execution
        frame = cv2.resize(frame, (1280, 720))
        results[frame_nmr] = {}
        # detect vehicles
        detections = coco_model(frame)[0]
        detections_ = []
        for detection in detections.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = detection
            if int(class_id) in vehicles:
                detections_.append([x1, y1, x2, y2, score])

        # track vehicles
        track_ids = mot_tracker.update(np.asarray(detections_))

        # draw vehicles
        for track in track_ids:
            xcar1, ycar1, xcar2, ycar2, car_id = track
            cv2.rectangle(frame, (int(xcar1), int(ycar1)), (int(xcar2), int(ycar2)), (0, 255, 0), 2)
            cv2.putText(frame, f"ID: {int(car_id)}", (int(xcar1), int(ycar1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # detect license plates
        license_plates = license_plate_detector(frame)[0]
        for license_plate in license_plates.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = license_plate

            # assign license plate to car
            xcar1, ycar1, xcar2, ycar2, car_id = get_car(license_plate, track_ids)

            if car_id != -1:
                # Check if we already have a confident reading for this car
                if car_id in best_license_plates and best_license_plates[car_id]['score'] > 0.8:
                    license_plate_text = best_license_plates[car_id]['text']
                    license_plate_text_score = best_license_plates[car_id]['score']
                else:
                    # crop license plate
                    license_plate_crop = frame[int(y1) : int(y2), int(x1) : int(x2), :]

                    # process license plate
                    license_plate_crop_gray = cv2.cvtColor(
                        license_plate_crop, cv2.COLOR_BGR2GRAY
                    )
                    _, license_plate_crop_thresh = cv2.threshold(
                        license_plate_crop_gray, 64, 255, cv2.THRESH_BINARY_INV
                    )

                    # read license plate number
                    license_plate_text, license_plate_text_score = read_license_plate(
                        license_plate_crop_thresh
                    )

                    if license_plate_text is not None:
                        if car_id not in best_license_plates or license_plate_text_score > best_license_plates[car_id]['score']:
                            best_license_plates[car_id] = {
                                'text': license_plate_text,
                                'score': license_plate_text_score
                            }

                if license_plate_text is not None:
                    # Draw license plate bounding box
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2)
                    # Draw read text above license plate
                    cv2.putText(frame, license_plate_text, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

                    results[frame_nmr][car_id] = {
                        "car": {"bbox": [xcar1, ycar1, xcar2, ycar2]},
                        "license_plate": {
                            "bbox": [x1, y1, x2, y2],
                            "text": license_plate_text,
                            "bbox_score": score,
                            "text_score": license_plate_text_score,
                        },
                    }

        # Display the frame live
        cv2.imshow('ANPR Live Detection (Press Q to quit)', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# write results
write_csv(results, "./test.csv")

cap.release()
cv2.destroyAllWindows()
