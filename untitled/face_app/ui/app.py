from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication


def create_app() -> QApplication:
    app = QApplication(sys.argv)
    app.setApplicationName("FaceGuard")
    app.setOrganizationName("SecureOrg")

    qss_path = Path(__file__).parent / "styles" / "main.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text())

    return app
