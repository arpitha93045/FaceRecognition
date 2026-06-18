from __future__ import annotations

import numpy as np
import insightface
from insightface.app import FaceAnalysis

from utils.config_loader import Config

_analyzer: FaceAnalysis | None = None


def get_analyzer() -> FaceAnalysis:
    global _analyzer
    if _analyzer is None:
        _analyzer = FaceAnalysis(name=Config.model_name, providers=["CPUExecutionProvider"])
        _analyzer.prepare(ctx_id=0, det_size=Config.det_size)
    return _analyzer


class FaceDetector:
    def __init__(self):
        self._app = get_analyzer()

    def detect(self, frame: np.ndarray) -> list:
        """Return insightface Face objects (each has .bbox, .kps, .embedding)."""
        if frame is None or frame.size == 0:
            return []
        faces = self._app.get(frame)
        return faces if faces is not None else []
