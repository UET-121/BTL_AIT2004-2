from engine.preprocessing import Preprocessor
from engine.postprocessing import Postprocessor
from engine.triton_client import TritonClient


class LicensePlatePipeline:
    def __init__(self):
        try:
            print("[*] Khởi tạo LicensePlatePipeline...")
            self.triton = TritonClient()
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
        yolo_input, pad_info = Preprocessor.process_for_yolo(frame)
        yolo_output = self.triton.detect_license_plates(yolo_input)
        result = Postprocessor.process_yolo_output(
            yolo_output, pad_info, self.conf, self.iou_thres
        )
        return result

    def embedding_frame(self, license_plate_img):
        arc_license_plate_input = Preprocessor.process_for_arcface(license_plate_img)
        arc_license_plate_output = self.triton.recognize_license_plate(arc_license_plate_input)
        vector = Postprocessor.process_arclicense_plate_output(arc_license_plate_output)
        return vector
