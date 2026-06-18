from __future__ import annotations

import time

import cv2
import numpy as np

from camera.source import CameraSource
from utils.config_loader import Config


class IPCameraSource(CameraSource):
    def __init__(self, url: str, label: str = "IP Camera"):
        self._url = url
        self._label = label
        self._cap: cv2.VideoCapture | None = None
        self._fail_count = 0
        self._max_fails = 3

    def open(self) -> bool:
        self._cap = cv2.VideoCapture(self._url)
        if self._cap.isOpened():
            self._fail_count = 0
            return True
        self._cap = None
        return False

    def read(self) -> tuple[bool, np.ndarray | None]:
        if self._cap is None or not self._cap.isOpened():
            return False, None

        ok, frame = self._cap.read()
        if not ok:
            self._fail_count += 1
            if self._fail_count >= self._max_fails:
                self._reconnect()
            return False, None

        self._fail_count = 0
        return True, frame

    def _reconnect(self) -> None:
        self.release()
        time.sleep(Config.reconnect_delay)
        self.open()

    def release(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    @property
    def name(self) -> str:
        return self._label

    @property
    def is_open(self) -> bool:
        return self._cap is not None and self._cap.isOpened()
