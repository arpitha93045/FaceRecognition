from __future__ import annotations

from PyQt6.QtWidgets import (
    QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QTabWidget, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QComboBox, QCheckBox, QDialog,
    QDialogButtonBox, QHeaderView,
)

import bcrypt

from db.connection import session_scope
from db.models import Camera, Role, User
from security.auth import auth_session
from security.audit import write_audit_log
from security.rbac import requires_role, Role as RoleEnum


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QLabel("Settings (Admin)")
        header.setObjectName("pageTitle")
        layout.addWidget(header)

        tabs = QTabWidget()
        tabs.addTab(self._build_user_tab(), "User Management")
        tabs.addTab(self._build_camera_tab(), "Camera Management")
        layout.addWidget(tabs)

    # ── User Management ───────────────────────────────────────────────────────

    def _build_user_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)

        toolbar = QHBoxLayout()
        btn_add = QPushButton("+ Add User")
        btn_add.setObjectName("primaryButton")
        btn_add.clicked.connect(self._on_add_user)
        toolbar.addWidget(btn_add)

        self._btn_del_user = QPushButton("Delete User")
        self._btn_del_user.setObjectName("dangerButton")
        self._btn_del_user.setEnabled(False)
        self._btn_del_user.clicked.connect(self._on_delete_user)
        toolbar.addWidget(self._btn_del_user)

        self._btn_chpwd = QPushButton("Change Password")
        self._btn_chpwd.setEnabled(False)
        self._btn_chpwd.clicked.connect(self._on_change_password)
        toolbar.addWidget(self._btn_chpwd)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        self._user_table = QTableWidget(0, 4)
        self._user_table.setHorizontalHeaderLabels(["ID", "Username", "Full Name", "Role"])
        self._user_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._user_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._user_table.setAlternatingRowColors(True)
        self._user_table.itemSelectionChanged.connect(self._on_user_selection)
        layout.addWidget(self._user_table)
        return w

    def _load_users(self):
        self._user_table.setRowCount(0)
        try:
            with session_scope() as session:
                users = session.query(User).filter_by(is_active=True).all()
                data = [u.to_dict() for u in users]
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return
        for d in data:
            row = self._user_table.rowCount()
            self._user_table.insertRow(row)
            for col, val in enumerate([str(d["id"]), d["username"], d["full_name"] or "", d["role"] or ""]):
                item = QTableWidgetItem(val)
                item.setData(0x100, d["id"])
                self._user_table.setItem(row, col, item)

    def _on_user_selection(self):
        has = len(self._user_table.selectedItems()) > 0
        self._btn_del_user.setEnabled(has)
        self._btn_chpwd.setEnabled(has)

    def _selected_user_id(self) -> int | None:
        items = self._user_table.selectedItems()
        return items[0].data(0x100) if items else None

    @requires_role(RoleEnum.ADMIN)
    def _on_add_user(self, _checked=False):
        dlg = _UserDialog(parent=self)
        if dlg.exec():
            self._load_users()

    @requires_role(RoleEnum.ADMIN)
    def _on_delete_user(self, _checked=False):
        uid = self._selected_user_id()
        if uid is None:
            return
        if uid == auth_session.user_id:
            QMessageBox.warning(self, "Error", "You cannot delete your own account.")
            return
        reply = QMessageBox.question(self, "Confirm", "Delete this user?")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with session_scope() as session:
                    u = session.get(User, uid)
                    if u:
                        u.is_active = False
                        write_audit_log("delete_user", "user", uid, {"username": u.username})
                self._load_users()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    @requires_role(RoleEnum.ADMIN)
    def _on_change_password(self, _checked=False):
        uid = self._selected_user_id()
        if uid is None:
            return
        dlg = _ChangePasswordDialog(uid, parent=self)
        dlg.exec()

    # ── Camera Management ─────────────────────────────────────────────────────

    def _build_camera_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)

        toolbar = QHBoxLayout()
        btn_add = QPushButton("+ Add Camera")
        btn_add.setObjectName("primaryButton")
        btn_add.clicked.connect(self._on_add_camera)
        toolbar.addWidget(btn_add)

        self._btn_del_cam = QPushButton("Delete Camera")
        self._btn_del_cam.setObjectName("dangerButton")
        self._btn_del_cam.setEnabled(False)
        self._btn_del_cam.clicked.connect(self._on_delete_camera)
        toolbar.addWidget(self._btn_del_cam)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self._cam_table = QTableWidget(0, 5)
        self._cam_table.setHorizontalHeaderLabels(["ID", "Name", "Location", "Type", "URI/Index"])
        self._cam_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._cam_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._cam_table.setAlternatingRowColors(True)
        self._cam_table.itemSelectionChanged.connect(
            lambda: self._btn_del_cam.setEnabled(len(self._cam_table.selectedItems()) > 0)
        )
        layout.addWidget(self._cam_table)
        return w

    def _load_cameras(self):
        self._cam_table.setRowCount(0)
        try:
            with session_scope() as session:
                cams = session.query(Camera).filter_by(is_active=True).all()
                data = [c.to_dict() for c in cams]
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return
        for d in data:
            row = self._cam_table.rowCount()
            self._cam_table.insertRow(row)
            uri_or_idx = d.get("source_uri") or str(d.get("device_index") or "0")
            for col, val in enumerate([
                str(d["id"]), d["name"], d.get("location") or "",
                d["source_type"], uri_or_idx,
            ]):
                item = QTableWidgetItem(val)
                item.setData(0x100, d["id"])
                self._cam_table.setItem(row, col, item)

    @requires_role(RoleEnum.ADMIN)
    def _on_add_camera(self, _checked=False):
        dlg = _CameraDialog(parent=self)
        if dlg.exec():
            self._load_cameras()

    @requires_role(RoleEnum.ADMIN)
    def _on_delete_camera(self, _checked=False):
        items = self._cam_table.selectedItems()
        if not items:
            return
        cid = items[0].data(0x100)
        reply = QMessageBox.question(self, "Confirm", "Remove this camera?")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with session_scope() as session:
                    cam = session.get(Camera, cid)
                    if cam:
                        cam.is_active = False
                self._load_cameras()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def on_shown(self):
        self._load_users()
        self._load_cameras()


# ── Helper dialogs ─────────────────────────────────────────────────────────────

class _UserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add User")
        self.setMinimumWidth(320)
        layout = QFormLayout(self)

        self._username = QLineEdit()
        self._full_name = QLineEdit()
        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._role = QComboBox()
        self._role.addItems(["operator", "admin"])

        layout.addRow("Username:", self._username)
        layout.addRow("Full Name:", self._full_name)
        layout.addRow("Password:", self._password)
        layout.addRow("Role:", self._role)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _save(self):
        uname = self._username.text().strip()
        pwd   = self._password.text()
        if not uname or not pwd:
            QMessageBox.warning(self, "Error", "Username and password are required.")
            return
        try:
            phash = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt(12)).decode()
            role_name = self._role.currentText()
            with session_scope() as session:
                role = session.query(Role).filter_by(name=role_name).first()
                user = User(
                    username=uname,
                    password_hash=phash,
                    full_name=self._full_name.text().strip() or None,
                    role_id=role.id,
                )
                session.add(user)
            write_audit_log("add_user", "user", detail={"username": uname})
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class _ChangePasswordDialog(QDialog):
    def __init__(self, user_id: int, parent=None):
        super().__init__(parent)
        self._user_id = user_id
        self.setWindowTitle("Change Password")
        self.setMinimumWidth(300)
        layout = QFormLayout(self)

        self._new_pwd = QLineEdit()
        self._new_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self._confirm = QLineEdit()
        self._confirm.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("New Password:", self._new_pwd)
        layout.addRow("Confirm:", self._confirm)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _save(self):
        p1 = self._new_pwd.text()
        p2 = self._confirm.text()
        if p1 != p2:
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return
        if len(p1) < 8:
            QMessageBox.warning(self, "Error", "Password must be at least 8 characters.")
            return
        try:
            phash = bcrypt.hashpw(p1.encode(), bcrypt.gensalt(12)).decode()
            with session_scope() as session:
                user = session.get(User, self._user_id)
                if user:
                    user.password_hash = phash
            write_audit_log("change_password", "user", self._user_id)
            QMessageBox.information(self, "Success", "Password changed.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class _CameraDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Camera")
        self.setMinimumWidth(380)
        layout = QFormLayout(self)

        self._name     = QLineEdit()
        self._location = QLineEdit()
        self._type     = QComboBox()
        self._type.addItems(["webcam", "rtsp", "http"])
        self._type.currentTextChanged.connect(self._on_type_changed)
        self._uri      = QLineEdit()
        self._uri.setPlaceholderText("rtsp://user:pass@ip:port/stream")
        self._idx      = QLineEdit("0")

        layout.addRow("Name:", self._name)
        layout.addRow("Location:", self._location)
        layout.addRow("Type:", self._type)
        self._uri_row_lbl = QLabel("Stream URL:")
        self._idx_row_lbl = QLabel("Device Index:")
        layout.addRow(self._uri_row_lbl, self._uri)
        layout.addRow(self._idx_row_lbl, self._idx)
        self._on_type_changed("webcam")

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _on_type_changed(self, t: str):
        is_webcam = t == "webcam"
        self._uri.setVisible(not is_webcam)
        self._uri_row_lbl.setVisible(not is_webcam)
        self._idx.setVisible(is_webcam)
        self._idx_row_lbl.setVisible(is_webcam)

    def _save(self):
        name = self._name.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Camera name is required.")
            return
        try:
            cam_type = self._type.currentText()
            with session_scope() as session:
                cam = Camera(
                    name=name,
                    location=self._location.text().strip() or None,
                    source_type=cam_type,
                    source_uri=self._uri.text().strip() or None if cam_type != "webcam" else None,
                    device_index=int(self._idx.text() or 0) if cam_type == "webcam" else None,
                )
                session.add(cam)
            write_audit_log("add_camera", "camera", detail={"name": name})
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
