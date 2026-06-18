from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from face_engine.detector import FaceDetector
from face_engine.matcher import EmbeddingMatcher
from ui.workers.search_worker import SearchWorker


class SearchPage(QWidget):
    def __init__(self, detector: FaceDetector, matcher: EmbeddingMatcher, parent=None):
        super().__init__(parent)
        self._detector = detector
        self._matcher = matcher
        self._worker: SearchWorker | None = None
        self._image_path: str | None = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel("Search by Image")
        header.setObjectName("pageTitle")
        layout.addWidget(header)

        top = QHBoxLayout()

        # ── Left: upload + thumbnail ──────────────────────────────────────────
        left = QVBoxLayout()
        self._img_label = QLabel("No image selected")
        self._img_label.setObjectName("imagePreview")
        self._img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_label.setFixedSize(260, 260)
        left.addWidget(self._img_label)

        btn_upload = QPushButton("Upload Image")
        btn_upload.clicked.connect(self._on_upload)
        left.addWidget(btn_upload)

        self._btn_search = QPushButton("Search")
        self._btn_search.setObjectName("primaryButton")
        self._btn_search.setEnabled(False)
        self._btn_search.clicked.connect(self._on_search)
        left.addWidget(self._btn_search)

        left.addStretch()
        top.addLayout(left)

        # ── Right: results table ──────────────────────────────────────────────
        right = QVBoxLayout()
        right.addWidget(QLabel("Matching Results"))

        self._result_table = QTableWidget(0, 5)
        self._result_table.setHorizontalHeaderLabels(
            ["Rank", "Name", "Service No.", "Department", "Match %"]
        )
        self._result_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._result_table.setAlternatingRowColors(True)
        self._result_table.horizontalHeader().setStretchLastSection(True)
        right.addWidget(self._result_table)

        top.addLayout(right, stretch=2)
        layout.addLayout(top)

    def _on_upload(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "",
            "Images (*.jpg *.jpeg *.png *.bmp *.webp)"
        )
        if not path:
            return
        self._image_path = path
        pix = QPixmap(path).scaled(
            260, 260, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._img_label.setPixmap(pix)
        self._btn_search.setEnabled(True)
        self._result_table.setRowCount(0)

    def _on_search(self):
        if not self._image_path:
            return
        self._btn_search.setEnabled(False)
        self._btn_search.setText("Searching…")

        self._worker = SearchWorker(
            image_path=self._image_path,
            detector=self._detector,
            matcher=self._matcher,
            top_k=5,
            parent=self,
        )
        self._worker.result_ready.connect(self._on_results)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(lambda: self._btn_search.setText("Search"))
        self._worker.start()

    def _on_results(self, results: list):
        self._result_table.setRowCount(0)
        self._btn_search.setEnabled(True)
        for rank, d in enumerate(results, 1):
            row = self._result_table.rowCount()
            self._result_table.insertRow(row)
            for col, val in enumerate([
                str(rank),
                d.get("full_name", ""),
                d.get("service_number", ""),
                d.get("department") or "",
                f"{d.get('score', 0):.1f}%",
            ]):
                self._result_table.setItem(row, col, QTableWidgetItem(val))

    def _on_error(self, msg: str):
        self._btn_search.setEnabled(True)
        QMessageBox.warning(self, "Search Error", msg)
