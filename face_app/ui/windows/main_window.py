from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QMainWindow, QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

from security.auth import auth_session


class MainWindow(QMainWindow):
    def __init__(self, detector, matcher, parent=None):
        super().__init__(parent)
        self._detector = detector
        self._matcher = matcher
        self.setWindowTitle("Face Recognition — Personnel Access System")
        self.setMinimumSize(1200, 750)
        self._build_ui()
        self._nav_list.setCurrentRow(0)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────────────────────
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        brand = QLabel("FaceGuard")
        brand.setObjectName("brand")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand.setFixedHeight(60)
        sidebar_layout.addWidget(brand)

        self._nav_list = QListWidget()
        self._nav_list.setObjectName("navList")
        nav_items = [
            ("Dashboard", True),
            ("Personnel", True),
            ("Live Recognition", True),
            ("Logs", True),
            ("Search by Image", True),
            ("Settings", auth_session.is_admin()),
        ]
        for label, visible in nav_items:
            item = QListWidgetItem(label)
            self._nav_list.addItem(item)
            if not visible:
                item.setHidden(True)
        self._nav_list.currentRowChanged.connect(self._on_nav_changed)
        sidebar_layout.addWidget(self._nav_list)

        sidebar_layout.addStretch()

        user_bar = QWidget()
        user_bar.setObjectName("userBar")
        ub_layout = QVBoxLayout(user_bar)
        ub_layout.setContentsMargins(12, 8, 12, 8)

        name_label = QLabel(f"{auth_session.full_name or auth_session.username}")
        name_label.setObjectName("userNameLabel")
        role_label = QLabel(f"Role: {auth_session.role or 'N/A'}")
        role_label.setObjectName("roleLabel")

        btn_logout = QPushButton("Logout")
        btn_logout.setObjectName("logoutButton")
        btn_logout.clicked.connect(self._on_logout)

        ub_layout.addWidget(name_label)
        ub_layout.addWidget(role_label)
        ub_layout.addWidget(btn_logout)
        sidebar_layout.addWidget(user_bar)

        root.addWidget(sidebar)

        # ── Main content area ─────────────────────────────────────────────────
        self._stack = QStackedWidget()
        root.addWidget(self._stack)

        self._pages: dict[str, QWidget] = {}
        self._load_pages()

    def _load_pages(self):
        from ui.windows.dashboard_page import DashboardPage
        from ui.windows.personnel_page import PersonnelPage
        from ui.windows.live_recognition_page import LiveRecognitionPage
        from ui.windows.logs_page import LogsPage
        from ui.windows.search_page import SearchPage
        from ui.windows.settings_page import SettingsPage

        pages = [
            ("Dashboard",        DashboardPage()),
            ("Personnel",        PersonnelPage(self._matcher)),
            ("Live Recognition", LiveRecognitionPage(self._detector, self._matcher)),
            ("Logs",             LogsPage()),
            ("Search by Image",  SearchPage(self._detector, self._matcher)),
            ("Settings",         SettingsPage()),
        ]
        for name, page in pages:
            self._pages[name] = page
            self._stack.addWidget(page)

        self._pages["Live Recognition"].detected_count_changed.connect(
            self._pages["Dashboard"].set_currently_detected
        )

    def _on_nav_changed(self, index: int):
        self._stack.setCurrentIndex(index)
        page_name = self._nav_list.item(index).text()
        page = self._pages.get(page_name)
        if page and hasattr(page, "on_shown"):
            page.on_shown()

    def _on_logout(self):
        auth_session.logout()
        self.close()

    def closeEvent(self, event):
        from PyQt6.QtWidgets import QApplication
        QApplication.instance().quit()
        super().closeEvent(event)
