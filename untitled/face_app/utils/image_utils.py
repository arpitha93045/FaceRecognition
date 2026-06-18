from __future__ import annotations

import cv2
import numpy as np
from PyQt6.QtGui import QImage, QPixmap


def numpy_to_pixmap(frame: np.ndarray) -> QPixmap:
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(img)


def draw_detection(
    frame: np.ndarray,
    bbox: list[int],
    label: str,
    confidence: float,
    known: bool,
) -> np.ndarray:
    x1, y1, x2, y2 = [int(v) for v in bbox]
    color = (0, 220, 0) if known else (0, 0, 220)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

    pct = f"{confidence * 100:.1f}%" if confidence > 0 else ""
    text = f"{label} {pct}".strip()

    font = cv2.FONT_HERSHEY_SIMPLEX
    scale, thickness = 0.55, 1
    (tw, th), baseline = cv2.getTextSize(text, font, scale, thickness)

    bg_y1 = max(y1 - th - baseline - 4, 0)
    cv2.rectangle(frame, (x1, bg_y1), (x1 + tw + 4, y1), color, -1)
    cv2.putText(frame, text, (x1 + 2, y1 - baseline - 2), font, scale, (255, 255, 255), thickness)

    return frame


def resize_frame(frame: np.ndarray, max_width: int = 960, max_height: int = 720) -> np.ndarray:
    h, w = frame.shape[:2]
    scale = min(max_width / w, max_height / h, 1.0)
    if scale < 1.0:
        new_w, new_h = int(w * scale), int(h * scale)
        frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return frame
