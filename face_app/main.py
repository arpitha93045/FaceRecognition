from __future__ import annotations

import sys
import logging
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtWidgets import QApplication, QSplashScreen, QLabel


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


class _ModelLoader(QThread):
    done    = pyqtSignal(object, object)   # detector, matcher
    failed  = pyqtSignal(str)

    def run(self):
        try:
            from face_engine.detector import FaceDetector
            from face_engine.matcher import EmbeddingMatcher
            from db.connection import session_scope

            detector = FaceDetector()
            matcher  = EmbeddingMatcher()
            with session_scope() as session:
                matcher.load(session)

            self.done.emit(detector, matcher)
        except Exception as e:
            self.failed.emit(str(e))


def main():
    # ── 1. Bootstrap config ───────────────────────────────────────────────────
    sys.path.insert(0, str(Path(__file__).parent))
    from utils.config_loader import Config
    log.setLevel(Config.log_level)

    # ── 2. Init database ──────────────────────────────────────────────────────
    from db.connection import init_db
    try:
        init_db(Config.db_url)
        log.info("Database connected.")
    except Exception as e:
        _fatal(f"Cannot connect to database:\n{e}\n\nCheck config.ini or DATABASE_URL.")
        return

    # ── 3. Start Qt app ───────────────────────────────────────────────────────
    from ui.app import create_app
    app = create_app()
    app.setQuitOnLastWindowClosed(False)  # prevent quit when login hides before main shows

    # ── 4. Splash screen while models load ────────────────────────────────────
    splash_lbl = QLabel("Loading AI models…\nPlease wait.")
    splash_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    splash_lbl.setFixedSize(420, 160)
    splash_lbl.setStyleSheet(
        "background:#1e1e2e; color:#89b4fa; font-size:16px; border-radius:12px;"
    )
    splash_lbl.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
    splash_lbl.show()

    loader = _ModelLoader()

    def _on_load_done(detector, matcher):
        splash_lbl.close()
        _show_login(app, detector, matcher)

    def _on_load_failed(msg: str):
        splash_lbl.close()
        _fatal(f"Failed to load AI models:\n{msg}")

    loader.done.connect(_on_load_done)
    loader.failed.connect(_on_load_failed)
    loader.start()

    sys.exit(app.exec())


def _show_login(app: QApplication, detector, matcher):
    from ui.windows.login_window import LoginWindow
    login = LoginWindow()
    # Store on app so GC never destroys it
    app._login_window = login

    def _on_success():
        try:
            from ui.windows.main_window import MainWindow
            win = MainWindow(detector=detector, matcher=matcher)
            app._main_window = win   # keep reference — prevents GC-triggered close
            win.show()
            login.hide()
        except Exception as e:
            import traceback
            _fatal(f"Failed to open main window:\n{traceback.format_exc()}")

    login.login_success.connect(_on_success)

    def _on_rejected():
        app.quit()

    login.rejected.connect(_on_rejected)
    login.show()


def _fatal(msg: str):
    from PyQt6.QtWidgets import QMessageBox
    QMessageBox.critical(None, "Fatal Error", msg)
    sys.exit(1)


if __name__ == "__main__":
    main()
