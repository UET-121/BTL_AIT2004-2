import cv2
import numpy as np


def assess_quality(image: np.ndarray) -> dict:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))
    return {
        "blur_score": blur_score,
        "brightness": brightness,
        "contrast": contrast,
        "is_blurry": blur_score < 100,
        "is_low_contrast": contrast < 40,
    }
