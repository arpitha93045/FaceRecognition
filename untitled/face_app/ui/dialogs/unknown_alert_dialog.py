from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
)


class UnknownAlertDialog(QDialog):
    def __init__(self, info: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Unknown Person Detected")
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        self.setMinimumWidth(340)
        self._build_ui(info)

    def _build_ui(self, info: dict):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        alert_lbl = QLabel("⚠ UNKNOWN PERSON DETECTED")
        alert_lbl.setObjectName("alertTitle")
        alert_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(alert_lbl)

        snap_path = info.get("snapshot_path")
        if snap_path and Path(snap_path).exists():
            pix = QPixmap(snap_path).scaled(
                200, 200, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            img_lbl = QLabel()
            img_lbl.setPixmap(pix)
            img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(img_lbl)

        score = info.get("best_score", 0)
        info_lbl = QLabel(f"Best match similarity: {score*100:.1f}%\nSnapshot saved.")
        info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_lbl)

        btn_ok = QPushButton("Dismiss")
        btn_ok.setObjectName("primaryButton")
        btn_ok.clicked.connect(self.accept)
        layout.addWidget(btn_ok)
