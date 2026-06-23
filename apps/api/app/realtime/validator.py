import logging
from collections import Counter
from app.services.factories import get_validator
from app.realtime.tracker import Track

logger = logging.getLogger(__name__)

class TemporalValidator:
    def __init__(self, min_confirm_count: int = 3, max_candidates: int = 8):
        self.validator = get_validator()
        self.min_confirm_count = min_confirm_count
        self.max_candidates = max_candidates

    def add_candidate(self, track: Track, text: str, confidence: float) -> tuple[str, str, float]:
        """
        Adds an OCR candidate to a track, checks if the plate is confirmed, rejected, or pending.
        Returns a tuple: (status, plate_text, confidence)
        status: "pending", "confirmed", "rejected"
        """
        if getattr(track, "is_rejected", False):
            consensus_text, avg_conf = self._get_consensus_text_and_conf(track)
            return "rejected", consensus_text, avg_conf

        if not text:
            # Empty read doesn't add to consensus but might contribute to progress
            if track.is_confirmed:
                consensus_text, avg_conf = self._get_consensus_text_and_conf(track)
                return "confirmed", consensus_text, avg_conf
            return "pending", "", 0.0

        # Validate format using configured rules (e.g., Brazilian plate regex)
        validation = self.validator.validate(text)
        cleaned_text = validation.corrected_text if validation.corrected_text else text
        is_valid = len(cleaned_text) >= 3 or validation.is_valid

        track.candidates.append({
            "text": cleaned_text,
            "confidence": confidence,
            "is_valid": is_valid
        })

        if track.is_confirmed:
            consensus_text, avg_conf = self._get_consensus_text_and_conf(track)
            return "confirmed", consensus_text, avg_conf

        # Separate candidates into valid and invalid format categories
        valid_candidates = [c for c in track.candidates if c["is_valid"]]

        if not valid_candidates:
            # If all candidates so far are invalid format and we hit max size limit, reject
            if len(track.candidates) >= self.max_candidates:
                consensus_text, avg_conf = self._get_consensus_text_and_conf(track)
                return "rejected", consensus_text, avg_conf
            consensus_text, avg_conf = self._get_consensus_text_and_conf(track)
            return "pending", consensus_text, avg_conf

        # Perform majority voting on valid candidate texts using the consensus helper
        most_common_text, avg_conf = self._get_consensus_text_and_conf(track)
        
        # Calculate count of the most common text in valid_candidates
        text_counts = Counter(c["text"] for c in valid_candidates)
        count = text_counts[most_common_text]

        if count >= self.min_confirm_count:
            track.is_confirmed = True
            return "confirmed", most_common_text, avg_conf

        if len(track.candidates) >= self.max_candidates:
            # Timeout / max attempts reached without high consensus format
            return "rejected", most_common_text, avg_conf

        return "pending", most_common_text, avg_conf

    def _get_consensus_text_and_conf(self, track: Track) -> tuple[str, float]:
        if not track.candidates:
            return "", 0.0
        
        # Prefer valid format text
        valid_candidates = [c for c in track.candidates if c["is_valid"]]
        target_list = valid_candidates if valid_candidates else track.candidates

        text_counts = Counter(c["text"] for c in target_list)
        most_common_text = text_counts.most_common(1)[0][0]

        matching_confs = [c["confidence"] for c in target_list if c["text"] == most_common_text]
        avg_conf = sum(matching_confs) / len(matching_confs) if matching_confs else 0.0

        return most_common_text, avg_conf

    def _get_consensus_text(self, track: Track) -> str:
        text, _ = self._get_consensus_text_and_conf(track)
        return text
