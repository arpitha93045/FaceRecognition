from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)


class PhotoUploadDialog(QDialog):
    """Stand-alone multi-photo upload dialog (reusable)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Upload Photos")
        self.setMinimumSize(500, 300)
        self.selected_paths: list[Path] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select one or more face images:"))

        btn_browse = QPushButton("Browse…")
        btn_browse.clicked.connect(self._on_browse)
        layout.addWidget(btn_browse)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._container = QWidget()
        self._thumb_layout = QHBoxLayout(self._container)
        self._thumb_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(self._container)
        layout.addWidget(scroll)

        self._count_label = QLabel("0 photos selected")
        layout.addWidget(self._count_label)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _on_browse(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Images", "",
            "Images (*.jpg *.jpeg *.png *.bmp *.webp)"
        )
        for path in paths:
            p = Path(path)
            if p not in self.selected_paths:
                self.selected_paths.append(p)
                pix = QPixmap(path).scaled(90, 90, Qt.AspectRatioMode.KeepAspectRatio)
                lbl = QLabel()
                lbl.setPixmap(pix)
                lbl.setToolTip(path)
                self._thumb_layout.addWidget(lbl)
        self._count_label.setText(f"{len(self.selected_paths)} photos selected")
