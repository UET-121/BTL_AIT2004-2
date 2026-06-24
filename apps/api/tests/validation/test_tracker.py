import pytest
from app.services.detection.detector import BoundingBox
from app.realtime.tracker import IoUTracker, compute_iou

def test_compute_iou():
    box_a = BoundingBox(x=0, y=0, width=10, height=10, confidence=0.9, class_name="plate")
    box_b = BoundingBox(x=5, y=0, width=10, height=10, confidence=0.8, class_name="plate")
    
    # Intersection is 5 * 10 = 50
    # Union is 100 + 100 - 50 = 150
    # IoU = 50 / 150 = 0.3333
    iou = compute_iou(box_a, box_b)
    assert abs(iou - 0.3333) < 0.001

    box_c = BoundingBox(x=20, y=20, width=10, height=10, confidence=0.9, class_name="plate")
    assert compute_iou(box_a, box_c) == 0.0

def test_iou_tracker_update():
    tracker = IoUTracker(max_lost_frames=2, min_iou=0.3)
    
    # Frame 1: spawn track 1
    det1 = BoundingBox(x=10, y=10, width=50, height=20, confidence=0.9)
    active = tracker.update([det1], frame_id=1)
    assert len(active) == 1
    assert 1 in active
    
    # Frame 2: track 1 moves slightly, should keep ID 1
    det2 = BoundingBox(x=12, y=11, width=50, height=20, confidence=0.85)
    active = tracker.update([det2], frame_id=2)
    assert len(active) == 1
    assert 1 in active

    # Frame 3: track 1 disappears, new box far away spawns track 2
    det3 = BoundingBox(x=100, y=100, width=50, height=20, confidence=0.95)
    active = tracker.update([det3], frame_id=3)
    assert len(active) == 1
    assert 2 in active
    assert 1 not in active  # track 1 is lost but not yet deleted (max_lost_frames = 2)
    
    # Frame 4: track 1 is now lost for 2 frames (last seen at frame 2, current frame 4)
    # The difference is 4 - 2 = 2. It should still be in the tracker tracks dict
    assert 1 in tracker.tracks
    
    # Frame 5: difference is 5 - 2 = 3 > max_lost_frames (2). It should be pruned.
    active = tracker.update([det3], frame_id=5)
    assert 1 not in tracker.tracks
