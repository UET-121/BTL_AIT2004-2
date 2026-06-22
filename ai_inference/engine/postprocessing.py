import cv2
import numpy as np


class Postprocessor:
    @staticmethod
    def process_yolo_output(output, pad_info, conf_threshold=0.5, iou_threshold=0.2):
        r, left, top, old_w, old_h = pad_info
        predictions = np.squeeze(output)

        scores = predictions[:, 4]
        valid_mask = scores > conf_threshold

        if not np.any(valid_mask):
            return {}

        valid_preds = predictions[valid_mask]
        valid_scores = valid_preds[:, 4].tolist()

        x1 = valid_preds[:, 0]
        y1 = valid_preds[:, 1]
        x2 = valid_preds[:, 2]
        y2 = valid_preds[:, 3]

        w = np.maximum(0.0, x2 - x1)
        h = np.maximum(0.0, y2 - y1)

        area_mask = (w > 0) & (h > 0)

        x1 = x1[area_mask]
        y1 = y1[area_mask]
        w = w[area_mask]
        h = h[area_mask]
        nms_scores = np.array(valid_scores)[area_mask].tolist()

        if len(nms_scores) == 0:
            return {}

        nms_boxes = np.stack([x1, y1, w, h], axis=1).tolist()

        indices = cv2.dnn.NMSBoxes(nms_boxes, nms_scores, conf_threshold, iou_threshold)

        result = []
        if len(indices) > 0:
            for i in indices.flatten():
                x1o = int((x1[i] - left) / r)
                y1o = int((y1[i] - top) / r)

                x2o = int((x1[i] + w[i] - left) / r)
                y2o = int((y1[i] + h[i] - top) / r)
                result.append(
                    {
                        "box": [
                            max(0, x1o),
                            max(0, y1o),
                            min(old_w, x2o),
                            min(old_h, y2o),
                        ],
                        "scores": nms_scores[i],
                    }
                )

        return result

    @staticmethod
    def process_arclicense_plate_output(embedding: np.ndarray) -> np.ndarray:
        embedding = np.squeeze(embedding)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding
