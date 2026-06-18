from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from camera.webcam import WebcamSource
from camera.ip_camera import IPCameraSource
from db.connection import session_scope
from db.models import Camera
from face_engine.detector import FaceDetector
from face_engine.matcher import EmbeddingMatcher
from ui.workers.recognition_worker import RecognitionWorker
from ui.dialogs.unknown_alert_dialog import UnknownAlertDialog
from utils.image_utils import numpy_to_pixmap
from utils.config_loader import Config


class LiveRecognitionPage(QWidget):
    detected_count_changed = pyqtSignal(int)  # emits face count on every detection update
    def __init__(self, detector: FaceDetector, matcher: EmbeddingMatcher, parent=None):
        super().__init__(parent)
        self._detector = detector
        self._matcher = matcher
        self._worker: RecognitionWorker | None = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QLabel("Live Recognition")
        header.setObjectName("pageTitle")
        layout.addWidget(header)

        # ── Controls ──────────────────────────────────────────────────────────
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("Camera:"))
        self._cam_combo = QComboBox()
        self._cam_combo.setMinimumWidth(220)
        ctrl.addWidget(self._cam_combo)
        ctrl.addStretch()

        self._btn_start = QPushButton("Start")
        self._btn_start.setObjectName("primaryButton")
        self._btn_start.clicked.connect(self._on_start)
        ctrl.addWidget(self._btn_start)

        self._btn_stop = QPushButton("Stop")
        self._btn_stop.setEnabled(False)
        self._btn_stop.clicked.connect(self._on_stop)
        ctrl.addWidget(self._btn_stop)

        layout.addLayout(ctrl)

        # ── Feed + detections ─────────────────────────────────────────────────
        content = QHBoxLayout()
        content.setSpacing(16)

        self._feed_label = QLabel("Camera feed will appear here")
        self._feed_label.setObjectName("cameraFeed")
        self._feed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._feed_label.setMinimumSize(640, 480)
        self._feed_label.setMaximumSize(960, 720)
        content.addWidget(self._feed_label, stretch=3)

        det_panel = QVBoxLayout()
        det_title = QLabel("Detected Personnel")
        det_title.setObjectName("sectionTitle")
        det_panel.addWidget(det_title)

        self._det_table = QTableWidget(0, 3)
        self._det_table.setHorizontalHeaderLabels(["Name", "Service No.", "Confidence"])
        self._det_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._det_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._det_table.horizontalHeader().setStretchLastSection(True)
        det_panel.addWidget(self._det_table)

        content.addLayout(det_panel, stretch=1)
        layout.addLayout(content)

    def _populate_cameras(self):
        self._cam_combo.clear()
        self._cam_combo.addItem("Default Webcam", userData=("webcam", 0, None))
        try:
            with session_scope() as session:
                cams = session.query(Camera).filter_by(is_active=True).all()
                for cam in cams:
                    label = f"{cam.name} ({cam.location or cam.source_type})"
                    self._cam_combo.addItem(label, userData=(cam.source_type, cam.device_index, cam.source_uri, cam.id))
        except Exception:
            pass

    def _on_start(self):
        self._populate_cameras()
        idx = self._cam_combo.currentIndex()
        data = self._cam_combo.itemData(idx)
        if data is None:
            data = ("webcam", 0, None)

        source_type = data[0]
        camera_db_id = data[3] if len(data) > 3 else None

        if source_type == "webcam":
            dev_idx = data[1] if data[1] is not None else Config.default_device_index
            camera = WebcamSource(dev_idx)
        else:
            uri = data[2]
            if not uri:
                QMessageBox.warning(self, "Error", "No URI configured for this camera.")
                return
            camera = IPCameraSource(uri, label=self._cam_combo.currentText())

        self._worker = RecognitionWorker(
            camera=camera,
            detector=self._detector,
            matcher=self._matcher,
            camera_db_id=camera_db_id,
            parent=self,
        )
        self._worker.frame_ready.connect(self._on_frame)
        self._worker.detections_ready.connect(self._on_detections)
        self._worker.unknown_detected.connect(self._on_unknown)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

        self._btn_start.setEnabled(False)
        self._btn_stop.setEnabled(True)

    def _on_stop(self):
        if self._worker:
            self._worker.stop()

    def _on_worker_finished(self):
        self._btn_start.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._feed_label.setText("Camera feed will appear here")
        self._det_table.setRowCount(0)
        self._worker = None
        self.detected_count_changed.emit(0)

    def _on_frame(self, frame):
        pixmap = numpy_to_pixmap(frame)
        self._feed_label.setPixmap(
            pixmap.scaled(
                self._feed_label.width(),
                self._feed_label.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _on_detections(self, results: list):
        self._det_table.setRowCount(0)
        for d in results:
            row = self._det_table.rowCount()
            self._det_table.insertRow(row)
            self._det_table.setItem(row, 0, QTableWidgetItem(d["name"]))
            self._det_table.setItem(row, 1, QTableWidgetItem(d["service_number"]))
            self._det_table.setItem(row, 2, QTableWidgetItem(f"{d['confidence']*100:.1f}%"))
        self.detected_count_changed.emit(len(results))

    def _on_unknown(self, info: dict):
        dlg = UnknownAlertDialog(info, parent=self)
        dlg.show()

    def on_shown(self):
        self._populate_cameras()

    def closeEvent(self, event):
        if self._worker:
            self._worker.stop()
        super().closeEvent(event)
