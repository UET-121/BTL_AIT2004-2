import logging
from pathlib import Path
import cv2
import numpy as np
import onnxruntime as ort

from app.services.detection.detector import BoundingBox, PlateDetector
from app.shared.config import Settings, get_settings

logger = logging.getLogger(__name__)

VEHICLE_CLASSES = {"car", "truck", "bus", "motorcycle"}
COCO_CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light",
    "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
    "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard",
    "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone",
    "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors", "teddy bear",
    "hair drier", "toothbrush"
]


def letterbox(img: np.ndarray, new_shape: tuple[int, int] = (640, 640), color: tuple[int, int, int] = (114, 114, 114)) -> tuple[np.ndarray, float, tuple[float, float]]:
    """Resize and pad image to a target shape while maintaining the aspect ratio."""
    shape = img.shape[:2]  # current shape [height, width]
    
    # Scale ratio (new / old)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])

    # Compute padding
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding

    dw /= 2  # divide padding into 2 sides
    dh /= 2

    if shape[::-1] != new_unpad:  # resize
        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)  # add border
    return img, r, (left, top)


class OnnxPlateDetector(PlateDetector):
    """ONNX-based license plate and vehicle detector with multiple execution provider support."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._plate_session = None
        self._vehicle_session = None

        # Probe available providers
        available_providers = ort.get_available_providers()
        logger.info("ONNX Runtime available providers: %s", available_providers)
        
        # Priority order
        priority = ["TensorrtExecutionProvider", "CUDAExecutionProvider", "DmlExecutionProvider", "CPUExecutionProvider"]
        self.providers = [p for p in priority if p in available_providers]
        if not self.providers:
            self.providers = ["CPUExecutionProvider"]
        
        # Optional manual override via settings or environment
        # (For example if custom onnx settings are wireable)
        logger.info("ONNX plate detector using providers: %s", self.providers)
        self._load_models()

    def _load_models(self) -> None:
        # 1. Load Custom Plate detection model
        plate_path = Path(self.settings.onnx_model_path)
        if not plate_path.exists():
            # Search fallback paths
            for p in [plate_path, Path("app") / plate_path, Path("apps/api") / plate_path]:
                if p.exists():
                    plate_path = p
                    break
        
        if plate_path.exists():
            try:
                self._plate_session = ort.InferenceSession(str(plate_path), providers=self.providers)
                logger.info("Loaded ONNX plate model from %s with providers %s", plate_path, self.providers)
            except Exception as exc:
                logger.warning(
                    "Failed to load ONNX plate model with providers %s: %s. Trying CPU fallback...",
                    self.providers,
                    exc
                )
                try:
                    self._plate_session = ort.InferenceSession(str(plate_path), providers=["CPUExecutionProvider"])
                    logger.info("Loaded ONNX plate model on CPU fallback")
                except Exception as fallback_exc:
                    logger.error("Failed to load ONNX plate model even on CPU: %s", fallback_exc)
        else:
            logger.warning("ONNX plate model not found at %s", self.settings.onnx_model_path)

        # 2. Load COCO Vehicle detection model
        # Default to yolov8n.onnx in the same folder as the plate model
        vehicle_path = plate_path.parent / "yolov8n.onnx"
        if not vehicle_path.exists():
            # Search alternative paths
            for p in [vehicle_path, Path("app/models/onnx/yolov8n.onnx"), Path("apps/api/models/onnx/yolov8n.onnx")]:
                if p.exists():
                    vehicle_path = p
                    break

        if vehicle_path.exists():
            try:
                self._vehicle_session = ort.InferenceSession(str(vehicle_path), providers=self.providers)
                logger.info("Loaded ONNX vehicle model from %s with providers %s", vehicle_path, self.providers)
            except Exception as exc:
                logger.warning(
                    "Failed to load ONNX vehicle model with providers %s: %s. Trying CPU fallback...",
                    self.providers,
                    exc
                )
                try:
                    self._vehicle_session = ort.InferenceSession(str(vehicle_path), providers=["CPUExecutionProvider"])
                    logger.info("Loaded ONNX vehicle model on CPU fallback")
                except Exception as fallback_exc:
                    logger.error("Failed to load ONNX vehicle model even on CPU: %s", fallback_exc)
        else:
            logger.warning("ONNX vehicle model not found at %s", vehicle_path)

    def is_loaded(self) -> bool:
        """Returns True if the required plate model session is successfully created."""
        return self._plate_session is not None

    def _run_inference(self, session: ort.InferenceSession, image: np.ndarray, imgsz: int = 640) -> tuple[np.ndarray, float, tuple[float, float]]:
        """Utility to run inference on an input image using a specific session."""
        # 1. Letterbox resize to input size (e.g. 640x640)
        padded_img, r, (pad_left, pad_top) = letterbox(image, (imgsz, imgsz))
        
        # 2. Convert BGR to RGB, normalize [0, 1], transpose to CHW
        input_data = cv2.cvtColor(padded_img, cv2.COLOR_BGR2RGB)
        input_data = input_data.astype(np.float32) / 255.0
        input_data = input_data.transpose(2, 0, 1)  # (3, imgsz, imgsz)
        input_data = np.expand_dims(input_data, axis=0)  # (1, 3, imgsz, imgsz)
        
        # 3. Get session inputs
        input_name = session.get_inputs()[0].name
        
        # 4. Inference
        outputs = session.run(None, {input_name: input_data})
        return outputs[0], r, (pad_left, pad_top)

    def _postprocess(self, output: np.ndarray, orig_shape: tuple[int, int], scale_ratio: float, pad: tuple[float, float], conf_threshold: float, is_vehicle: bool = False) -> list[BoundingBox]:
        """Post-process YOLOv8 output tensor to a list of BoundingBoxes, applying NMS."""
        # Output shape is (1, 4 + classes, 8400) or similar. Transpose to (8400, 4 + classes)
        output = output[0].T
        
        bboxes = []
        scores_list = []
        class_ids = []
        
        h_orig, w_orig = orig_shape
        pad_left, pad_top = pad
        
        if is_vehicle:
            class_scores = output[:, 4:]
            max_scores = np.max(class_scores, axis=1)
            class_ids_all = np.argmax(class_scores, axis=1)
            
            keep = max_scores > conf_threshold
            filtered_output = output[keep]
            filtered_scores = max_scores[keep]
            filtered_class_ids = class_ids_all[keep]
            
            if len(filtered_output) > 0:
                x_center = filtered_output[:, 0]
                y_center = filtered_output[:, 1]
                w = filtered_output[:, 2]
                h = filtered_output[:, 3]
                
                x1 = x_center - w / 2
                y1 = y_center - h / 2
                
                x1_orig = ((x1 - pad_left) / scale_ratio).astype(np.int32)
                y1_orig = ((y1 - pad_top) / scale_ratio).astype(np.int32)
                w_orig_boxes = (w / scale_ratio).astype(np.int32)
                h_orig_boxes = (h / scale_ratio).astype(np.int32)
                
                for i in range(len(filtered_output)):
                    c_id = int(filtered_class_ids[i])
                    c_name = COCO_CLASSES[c_id] if c_id < len(COCO_CLASSES) else "unknown"
                    if c_name in VEHICLE_CLASSES:
                        bboxes.append([int(x1_orig[i]), int(y1_orig[i]), int(w_orig_boxes[i]), int(h_orig_boxes[i])])
                        scores_list.append(float(filtered_scores[i]))
                        class_ids.append((c_id, c_name))
        else:
            scores = output[:, 4]
            keep = scores > conf_threshold
            filtered_output = output[keep]
            filtered_scores = scores[keep]
            
            if len(filtered_output) > 0:
                x_center = filtered_output[:, 0]
                y_center = filtered_output[:, 1]
                w = filtered_output[:, 2]
                h = filtered_output[:, 3]
                
                x1 = x_center - w / 2
                y1 = y_center - h / 2
                
                x1_orig = ((x1 - pad_left) / scale_ratio).astype(np.int32)
                y1_orig = ((y1 - pad_top) / scale_ratio).astype(np.int32)
                w_orig_boxes = (w / scale_ratio).astype(np.int32)
                h_orig_boxes = (h / scale_ratio).astype(np.int32)
                
                for i in range(len(filtered_output)):
                    bboxes.append([int(x1_orig[i]), int(y1_orig[i]), int(w_orig_boxes[i]), int(h_orig_boxes[i])])
                    scores_list.append(float(filtered_scores[i]))
                    class_ids.append((0, "plate"))
                    
        if not bboxes:
            return []
            
        # Fast OpenCV Non-Maximum Suppression (C++ implementation)
        indices = cv2.dnn.NMSBoxes(bboxes, scores_list, conf_threshold, 0.45)
        
        # Normalize indices array across OpenCV versions
        if isinstance(indices, np.ndarray):
            indices = indices.flatten()
        elif isinstance(indices, tuple) or isinstance(indices, list):
            indices = list(indices)
        else:
            indices = []
            
        boxes = []
        for idx in indices:
            x, y, w, h = bboxes[idx]
            conf = scores_list[idx]
            _, class_name = class_ids[idx]
            
            bbox = BoundingBox(
                x=x,
                y=y,
                width=w,
                height=h,
                confidence=conf,
                class_name=class_name
            ).clamp_to_image(h_orig, w_orig)
            boxes.append(bbox)
            
        return boxes

    def detect(self, image: np.ndarray) -> list[BoundingBox]:
        if not self.settings.use_plate_detection:
            return self._tier3_full_image(image, tier=3)

        boxes: list[BoundingBox] = []
        tier_used = 3

        if self._plate_session is not None:
            boxes = self._tier1_plate_detection(image)
            if boxes:
                tier_used = 1

        if not boxes and self._vehicle_session is not None:
            boxes = self._tier2_vehicle_detection(image)
            if boxes:
                tier_used = 2

        if not boxes:
            boxes = self._tier3_full_image(image, tier=3)
            tier_used = 3

        for box in boxes:
            box.class_name = f"{box.class_name}:tier{tier_used}"

        return boxes

    def detect_vehicles_and_plates(self, image: np.ndarray) -> list[dict]:
        """Detects both vehicles and license plates and associates them."""
        h, w = image.shape[:2]
        plates_detected = []

        # 1. Run plate detection (custom model) first if configured
        is_custom_plate_model = self.settings.plate_detection_model != "yolov8n.pt"
        if is_custom_plate_model and self._plate_session is not None:
            output, r, pad = self._run_inference(self._plate_session, image, imgsz=640)
            plates_detected = self._postprocess(
                output, 
                image.shape[:2], 
                r, 
                pad, 
                self.settings.plate_detection_confidence, 
                is_vehicle=False
            )
            for plate in plates_detected:
                plate.class_name = "plate"

        # 2. If plates are detected, we bypass the COCO vehicle detection model pass to save CPU!
        if plates_detected:
            associated_results = []
            for plt in plates_detected:
                veh_bbox = BoundingBox(
                    x=max(0, plt.x - plt.width),
                    y=max(0, plt.y - plt.height * 2),
                    width=plt.width * 3,
                    height=plt.height * 4,
                    confidence=plt.confidence,
                    class_name="car"
                ).clamp_to_image(h, w)
                associated_results.append({
                    "vehicle_bbox": veh_bbox,
                    "plate_bbox": plt,
                    "vehicle_conf": plt.confidence * 0.8,
                    "plate_conf": plt.confidence,
                    "class_name": "car"
                })
            return associated_results

        # 3. Fallback: Run vehicle detection (if no plates found or not using custom plate model)
        vehicles_detected = []
        if self._vehicle_session is not None:
            # ONNX model requires the static 640x640 shape exported by default
            output, r, pad = self._run_inference(self._vehicle_session, image, imgsz=640)
            vehicles_detected = self._postprocess(
                output, 
                image.shape[:2], 
                r, 
                pad, 
                0.5, 
                is_vehicle=True
            )

        # 4. Associate vehicles with estimated plate region if no plates were detected directly
        associated_results = []
        for veh in vehicles_detected:
            vehicle_h = veh.height
            plate_y1 = veh.y + int(vehicle_h * 0.7)
            plate_y2 = veh.y + vehicle_h
            plate_bbox = BoundingBox(
                x=veh.x,
                y=plate_y1,
                width=veh.width,
                height=max(1, plate_y2 - plate_y1),
                confidence=veh.confidence * 0.8,
                class_name="vehicle_plate_region"
            ).clamp_to_image(h, w)
            associated_results.append({
                "vehicle_bbox": veh,
                "plate_bbox": plate_bbox,
                "vehicle_conf": veh.confidence,
                "plate_conf": veh.confidence * 0.8,
                "class_name": veh.class_name
            })

        if not associated_results:
            full_box = BoundingBox(
                x=0,
                y=0,
                width=w,
                height=h,
                confidence=0.5,
                class_name="full_image"
            )
            associated_results.append({
                "vehicle_bbox": full_box,
                "plate_bbox": full_box,
                "vehicle_conf": 0.5,
                "plate_conf": 0.5,
                "class_name": "car"
            })

        return associated_results

    def _tier1_plate_detection(self, image: np.ndarray) -> list[BoundingBox]:
        if self._plate_session is None:
            return []
        output, r, pad = self._run_inference(self._plate_session, image, imgsz=640)
        boxes = self._postprocess(
            output, 
            image.shape[:2], 
            r, 
            pad, 
            self.settings.plate_detection_confidence, 
            is_vehicle=False
        )
        for box in boxes:
            box.class_name = "plate"
        boxes.sort(key=lambda b: b.confidence, reverse=True)
        return boxes

    def _tier2_vehicle_detection(self, image: np.ndarray) -> list[BoundingBox]:
        if self._vehicle_session is None:
            return []
        # ONNX model requires the static 640x640 shape exported by default
        output, r, pad = self._run_inference(self._vehicle_session, image, imgsz=640)
        boxes = self._postprocess(
            output, 
            image.shape[:2], 
            r, 
            pad, 
            self.settings.plate_detection_confidence, 
            is_vehicle=True
        )
        
        fallback_boxes = []
        h, w = image.shape[:2]
        for veh in boxes:
            vehicle_h = veh.height
            plate_y1 = veh.y + int(vehicle_h * 0.7)
            plate_y2 = veh.y
            bbox = BoundingBox(
                x=veh.x,
                y=plate_y1,
                width=veh.width,
                height=max(1, plate_y2 - plate_y1),
                confidence=veh.confidence * 0.8,
                class_name="vehicle_plate_region",
            ).clamp_to_image(h, w)
            fallback_boxes.append(bbox)

        fallback_boxes.sort(key=lambda b: b.confidence, reverse=True)
        return fallback_boxes[:1]

    def _tier3_full_image(self, image: np.ndarray, tier: int = 3) -> list[BoundingBox]:
        h, w = image.shape[:2]
        return [
            BoundingBox(
                x=0,
                y=0,
                width=w,
                height=h,
                confidence=0.5,
                class_name=f"full_image:tier{tier}",
            )
        ]
