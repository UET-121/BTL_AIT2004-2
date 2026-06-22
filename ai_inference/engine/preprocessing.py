import cv2
import numpy as np


class Preprocessor:
    @staticmethod
    def process_for_yolo(image: np.ndarray, target_size=(640, 640)):
        old_h, old_w = image.shape[:2]

        r = min(target_size[0] / old_w, target_size[1] / old_h)
        new_unpad_w = int(round(old_w * r))
        new_unpad_h = int(round(old_h * r))

        im = cv2.resize(
            image, (new_unpad_w, new_unpad_h), interpolation=cv2.INTER_LINEAR
        )

        dw = target_size[0] - new_unpad_w
        dh = target_size[1] - new_unpad_h

        top, bottom = dh // 2, dh - (dh // 2)
        left, right = dw // 2, dw - (dw // 2)

        im = cv2.copyMakeBorder(
            im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114)
        )

        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        im = im.astype(np.float32) / 255.0
        im = np.expand_dims(im, axis=0)

        pad_info = (r, left, top, old_w, old_h)

        return im, pad_info

    @staticmethod
    def process_for_arcface(
        license_plate_crop: np.ndarray, target_size=(112, 112)
    ) -> np.ndarray:

        im = cv2.resize(license_plate_crop, target_size)
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)

        im = im.astype(np.float32)
        im = (im - 127.5) / 127.5

        im = np.expand_dims(im, axis=0)

        return im
