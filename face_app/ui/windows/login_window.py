from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QHBoxLayout, QWidget,
)

from security.auth import auth_session


class LoginWindow(QDialog):
    login_success = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Face Recognition System — Login")
        self.setFixedSize(380, 280)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 32, 40, 32)

        title = QLabel("Face Recognition System")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(13)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        sub = QLabel("Personnel Access Monitoring")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setObjectName("subtitle")
        layout.addWidget(sub)

        layout.addSpacing(8)

        form = QFormLayout()
        form.setSpacing(10)

        self._username = QLineEdit()
        self._username.setPlaceholderText("Username")
        self._username.setMinimumHeight(32)
        form.addRow("Username:", self._username)

        self._password = QLineEdit()
        self._password.setPlaceholderText("Password")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setMinimumHeight(32)
        self._password.returnPressed.connect(self._on_login)
        form.addRow("Password:", self._password)

        layout.addLayout(form)

        self._error_label = QLabel("")
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.setObjectName("errorLabel")
        layout.addWidget(self._error_label)

        btn_login = QPushButton("Login")
        btn_login.setMinimumHeight(36)
        btn_login.setObjectName("primaryButton")
        btn_login.clicked.connect(self._on_login)
        layout.addWidget(btn_login)

    def _on_login(self):
        username = self._username.text().strip()
        password = self._password.text()
        if not username or not password:
            self._show_error("Please enter username and password.")
            return
        if auth_session.login(username, password):
            self._error_label.setText("")
            self.login_success.emit()
            self.accept()
        else:
            self._show_error("Invalid username or password.")
            self._password.clear()

    def _show_error(self, msg: str):
        self._error_label.setText(msg)
