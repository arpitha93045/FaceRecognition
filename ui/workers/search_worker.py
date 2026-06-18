from __future__ import annotations

import cv2
from PyQt6.QtCore import QThread, pyqtSignal

from face_engine.detector import FaceDetector
from face_engine.embedder import extract_embedding
from face_engine.matcher import EmbeddingMatcher
from db.connection import session_scope
from db.models import Personnel


class SearchWorker(QThread):
    result_ready = pyqtSignal(list)   # list[dict]: personnel info + score
    error        = pyqtSignal(str)

    def __init__(
        self,
        image_path: str,
        detector: FaceDetector,
        matcher: EmbeddingMatcher,
        top_k: int = 5,
        parent=None,
    ):
        super().__init__(parent)
        self._image_path = image_path
        self._detector = detector
        self._matcher = matcher
        self._top_k = top_k

    def run(self):
        frame = cv2.imread(self._image_path)
        if frame is None:
            self.error.emit("Could not read the selected image file.")
            return

        faces = self._detector.detect(frame)
        if not faces:
            self.error.emit("No face detected in the uploaded image.")
            return

        # Use the largest face
        largest = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
        emb = extract_embedding(largest)
        matches = self._matcher.search_top_k(emb, k=self._top_k)

        if not matches:
            self.result_ready.emit([])
            return

        results = []
        try:
            with session_scope() as session:
                for m in matches:
                    person = session.get(Personnel, m.personnel_id)
                    if person:
                        d = person.to_dict()
                        d["score"] = round(m.score * 100, 1)
                        results.append(d)
        except Exception as e:
            self.error.emit(f"Database error: {e}")
            return

        self.result_ready.emit(results)
