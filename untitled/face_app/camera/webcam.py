from __future__ import annotations

import cv2
import numpy as np

from camera.source import CameraSource


class WebcamSource(CameraSource):
    def __init__(self, device_index: int = 0):
        self._index = device_index
        self._cap: cv2.VideoCapture | None = None

    def open(self) -> bool:
        self._cap = cv2.VideoCapture(self._index)
        if not self._cap.isOpened():
            self._cap = None
            return False
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return True

    def read(self) -> tuple[bool, np.ndarray | None]:
        if self._cap is None or not self._cap.isOpened():
            return False, None
        ok, frame = self._cap.read()
        return ok, frame if ok else None

    def release(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    @property
    def name(self) -> str:
        return f"Webcam #{self._index}"

    @property
    def is_open(self) -> bool:
        return self._cap is not None and self._cap.isOpened()
