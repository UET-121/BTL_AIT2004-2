from engine.preprocessing import Preprocessor
from engine.postprocessing import Postprocessor
from engine.triton_client import TritonClient
from engine.easyocr_engine import EasyOCREngine
import cv2
import numpy as np

class LicensePlatePipeline:
    def __init__(self):
        try:
            print("[*] Khởi tạo LicensePlatePipeline với Triton YOLO và EasyOCR...")
            self.triton = TritonClient()
            
            class SettingsMock:
                ocr_gpu = True
                ocr_min_confidence = 0.2
            
            self.ocr_engine = EasyOCREngine(settings=SettingsMock())
        except Exception as e:
            print(f"[X] Lỗi khi khởi tạo LicensePlatePipeline: {e}")
            raise e
        self.conf = 0.5
        self.iou_thres = 0.2

    def update_thres(self, conf: float = None, iou_thres: float = None):
        if conf:
            self.conf = conf
        if iou_thres:
            self.iou_thres = iou_thres

    def detect_frame(self, frame):
        # Use Triton for YOLO inference to maximize GPU optimization
        yolo_input, pad_info = Preprocessor.process_for_yolo(frame)
        yolo_output = self.triton.detect_license_plates(yolo_input)
        
        # Raw boxes processed into nice output
        result = Postprocessor.process_yolo_output(
            yolo_output, pad_info, self.conf, self.iou_thres
        )
        
        # Format for streamer: [ { "box": [x1, y1, x2, y2], "scores": conf, "class_name": "plate" } ]
        formatted_result = []
        for det in result:
            formatted_result.append({
                "box": det["box"],
                "scores": det["scores"],
                "class_name": "plate"
            })
        return formatted_result

    def recognize_plate(self, license_plate_img):
        # Local OCR running on GPU
        ocr_result = self.ocr_engine.read(license_plate_img)
        return ocr_result.text
