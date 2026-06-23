import pytest
from app.services.detection.detector import BoundingBox
from app.realtime.tracker import Track
from app.realtime.validator import TemporalValidator

def test_temporal_validator_consensus():
    validator = TemporalValidator(min_confirm_count=3, max_candidates=5)
    bbox = BoundingBox(x=10, y=10, width=50, height=20, confidence=0.9)
    track = Track(track_id=1, bbox=bbox, frame_id=1)

    # 1. Add first candidate - should be pending
    status, plate, conf = validator.add_candidate(track, "ABC1D23", 0.9)
    assert status == "pending"
    assert plate == "ABC1D23"
    assert conf == 0.9

    # 2. Add second candidate - should still be pending
    status, plate, conf = validator.add_candidate(track, "ABC1D23", 0.8)
    assert status == "pending"
    assert plate == "ABC1D23"
    assert abs(conf - 0.85) < 0.001

    # 3. Add third candidate (different text) - should still be pending
    status, plate, conf = validator.add_candidate(track, "ABC1D24", 0.7)
    assert status == "pending"
    assert plate == "ABC1D23"  # most common is still ABC1D23 (2 votes vs 1)

    # 4. Add third matching candidate - should reach min_confirm_count = 3 and confirm
    status, plate, conf = validator.add_candidate(track, "ABC1D23", 0.85)
    assert status == "confirmed"
    assert plate == "ABC1D23"
    assert track.is_confirmed is True

def test_temporal_validator_rejection():
    validator = TemporalValidator(min_confirm_count=3, max_candidates=4)
    bbox = BoundingBox(x=10, y=10, width=50, height=20, confidence=0.9)
    track = Track(track_id=2, bbox=bbox, frame_id=1)

    # Add all invalid/varying text candidates up to max_candidates
    validator.add_candidate(track, "XYZ9999", 0.5)
    validator.add_candidate(track, "XYZ8888", 0.6)
    validator.add_candidate(track, "XYZ7777", 0.4)
    status, plate, conf = validator.add_candidate(track, "XYZ6666", 0.5)

    # Max candidates (4) reached without hitting min_confirm_count (3), should reject
    assert status == "rejected"
