from __future__ import annotations

import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

from camera.source import CameraSource
from db.connection import session_scope
from db.models import AttendanceLog, UnknownDetection
from face_engine.detector import FaceDetector
from face_engine.embedder import extract_embedding
from face_engine.matcher import EmbeddingMatcher
from security.auth import auth_session
from utils.config_loader import Config
from utils.image_utils import draw_detection, resize_frame

ATTENDANCE_COOLDOWN_SEC = 60


class RecognitionWorker(QThread):
    frame_ready       = pyqtSignal(object)   # np.ndarray — resized display frame
    detections_ready  = pyqtSignal(list)     # list[dict]
    unknown_detected  = pyqtSignal(dict)

    def __init__(
        self,
        camera: CameraSource,
        detector: FaceDetector,
        matcher: EmbeddingMatcher,
        camera_db_id: int | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._camera = camera
        self._detector = detector
        self._matcher = matcher
        self._camera_db_id = camera_db_id
        self._stop_flag = False
        self._last_logged: dict[int, datetime] = {}
        self._frame_skip = Config.frame_skip

    def run(self):
        if not self._camera.open():
            return

        frame_count = 0
        while not self._stop_flag:
            ok, frame = self._camera.read()
            if not ok or frame is None:
                time.sleep(0.01)
                continue

            display_frame = resize_frame(frame.copy())
            frame_count += 1

            if frame_count % self._frame_skip == 0:
                faces = self._detector.detect(frame)
                results = []

                for face in faces:
                    emb = extract_embedding(face)
                    match = self._matcher.match(emb)
                    bbox = face.bbox.astype(int).tolist()

                    if match:
                        draw_detection(display_frame, bbox, match.full_name, match.score, known=True)
                        results.append({
                            "personnel_id": match.personnel_id,
                            "name": match.full_name,
                            "service_number": match.service_number,
                            "confidence": match.score,
                            "bbox": bbox,
                        })
                        self._maybe_log_attendance(match.personnel_id, match.score)
                    else:
                        draw_detection(display_frame, bbox, "UNKNOWN", 0.0, known=False)
                        snap_path = self._save_snapshot(frame, bbox)
                        self.unknown_detected.emit({
                            "snapshot_path": snap_path,
                            "best_score": self._matcher.last_best_score,
                            "bbox": bbox,
                        })
                        self._log_unknown(snap_path)

                if results:
                    self.detections_ready.emit(results)

            self.frame_ready.emit(display_frame)

        self._camera.release()

    def stop(self):
        self._stop_flag = True
        self.wait()

    def _maybe_log_attendance(self, personnel_id: int, score: float) -> None:
        now = datetime.utcnow()
        last = self._last_logged.get(personnel_id)
        if last is not None and (now - last).total_seconds() < ATTENDANCE_COOLDOWN_SEC:
            return
        self._last_logged[personnel_id] = now
        try:
            with session_scope() as session:
                log = AttendanceLog(
                    personnel_id=personnel_id,
                    camera_id=self._camera_db_id,
                    event_type="entry",
                    confidence=round(score, 4),
                )
                session.add(log)
        except Exception as e:
            print(f"[Worker] Failed to log attendance: {e}")

    def _log_unknown(self, snapshot_path: str | None) -> None:
        try:
            with session_scope() as session:
                row = UnknownDetection(
                    camera_id=self._camera_db_id,
                    snapshot_path=snapshot_path,
                    best_score=round(self._matcher.last_best_score, 4),
                )
                session.add(row)
        except Exception as e:
            print(f"[Worker] Failed to log unknown: {e}")

    def _save_snapshot(self, frame: np.ndarray, bbox: list[int]) -> str | None:
        try:
            snap_dir = Config.snapshot_dir
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
            path = snap_dir / f"unknown_{ts}.jpg"
            x1, y1, x2, y2 = [max(0, v) for v in bbox]
            crop = frame[y1:y2, x1:x2]
            if crop.size > 0:
                cv2.imwrite(str(path), crop)
            else:
                cv2.imwrite(str(path), frame)
            return str(path)
        except Exception:
            return None
