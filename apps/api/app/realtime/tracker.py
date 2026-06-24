import logging
from app.services.detection.detector import BoundingBox

logger = logging.getLogger(__name__)

def compute_iou(box_a: BoundingBox, box_b: BoundingBox) -> float:
    """Computes Intersection over Union (IoU) between two bounding boxes."""
    x_a = max(box_a.x, box_b.x)
    y_a = max(box_a.y, box_b.y)
    x_b = min(box_a.x + box_a.width, box_b.x + box_b.width)
    y_b = min(box_a.y + box_a.height, box_b.y + box_b.height)

    inter_area = max(0, x_b - x_a) * max(0, y_b - y_a)
    box_a_area = box_a.width * box_a.height
    box_b_area = box_b.width * box_b.height
    union_area = float(box_a_area + box_b_area - inter_area)

    if union_area <= 0:
        return 0.0

    return inter_area / union_area

class Track:
    def __init__(self, track_id: int, bbox: BoundingBox, frame_id: int, plate_bbox: BoundingBox | None = None, vehicle_conf: float = 1.0, plate_conf: float = 1.0, class_name: str = "car"):
        self.track_id = track_id
        self.bbox = bbox
        self.first_seen = frame_id
        self.last_seen = frame_id
        self.hits = 1
        # Store raw OCR candidates: list of dicts: {"text": str, "confidence": float}
        self.candidates: list[dict] = []
        # Flag to indicate if this track has already broadcasted a "plate.confirmed" event
        self.is_confirmed = False
        # Flag to indicate if this track has already been rejected (reaches max candidates without consensus)
        self.is_rejected = False
        
        # Enhanced tracking fields
        self.plate_bbox = plate_bbox if plate_bbox is not None else bbox
        self.vehicle_conf = vehicle_conf
        self.plate_conf = plate_conf
        self.class_name = class_name

class IoUTracker:
    def __init__(self, max_lost_frames: int = 15, min_iou: float = 0.3):
        self.max_lost_frames = max_lost_frames
        self.min_iou = min_iou
        self.next_track_id = 1
        self.tracks: dict[int, Track] = {}

    def update(self, detections: list[BoundingBox | dict], frame_id: int) -> dict[int, BoundingBox]:
        """Updates tracks with new detections and returns mapping of track_id to current bbox."""
        # Normalize detections to dictionaries
        normalized_detections = []
        for det in detections:
            if isinstance(det, BoundingBox):
                normalized_detections.append({
                    "vehicle_bbox": det,
                    "plate_bbox": det,
                    "vehicle_conf": det.confidence,
                    "plate_conf": det.confidence,
                    "class_name": det.class_name
                })
            else:
                normalized_detections.append(det)

        active_track_ids = list(self.tracks.keys())
        matched_detections = set()
        matched_tracks = set()

        matches = []
        for track_id in active_track_ids:
            track = self.tracks[track_id]
            for j, det in enumerate(normalized_detections):
                iou = compute_iou(track.bbox, det["vehicle_bbox"])
                if iou >= self.min_iou:
                    matches.append((iou, track_id, j))

        # Sort matches by highest overlap first
        matches.sort(key=lambda x: x[0], reverse=True)

        for iou, track_id, det_idx in matches:
            if track_id in matched_tracks or det_idx in matched_detections:
                continue
            matched_tracks.add(track_id)
            matched_detections.add(det_idx)
            
            # Update matching track
            track = self.tracks[track_id]
            det = normalized_detections[det_idx]
            track.bbox = det["vehicle_bbox"]
            track.plate_bbox = det["plate_bbox"]
            track.vehicle_conf = det["vehicle_conf"]
            track.plate_conf = det["plate_conf"]
            track.class_name = det["class_name"]
            track.last_seen = frame_id
            track.hits += 1

        # Spawn new tracks for remaining unmatched detections
        for j, det in enumerate(normalized_detections):
            if j not in matched_detections:
                new_track = Track(
                    self.next_track_id,
                    det["vehicle_bbox"],
                    frame_id,
                    plate_bbox=det["plate_bbox"],
                    vehicle_conf=det["vehicle_conf"],
                    plate_conf=det["plate_conf"],
                    class_name=det["class_name"]
                )
                self.tracks[self.next_track_id] = new_track
                self.next_track_id += 1

        # Prune stale tracks
        stale_ids = []
        for track_id, track in self.tracks.items():
            if frame_id - track.last_seen > self.max_lost_frames:
                stale_ids.append(track_id)

        for track_id in stale_ids:
            del self.tracks[track_id]

        # Get all active bounding boxes for the current frame
        active_now = {}
        for track_id, track in self.tracks.items():
            if track.last_seen == frame_id:
                active_now[track_id] = track.bbox

        return active_now

