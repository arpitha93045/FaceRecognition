from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QHeaderView,
)

from db.connection import session_scope
from db.models import Personnel, Department
from face_engine.matcher import EmbeddingMatcher
from security.auth import auth_session
from security.audit import write_audit_log
from security.rbac import Role, requires_role


class PersonnelPage(QWidget):
    def __init__(self, matcher: EmbeddingMatcher, parent=None):
        super().__init__(parent)
        self._matcher = matcher
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QLabel("Personnel Management")
        header.setObjectName("pageTitle")
        layout.addWidget(header)

        # ── Toolbar ───────────────────────────────────────────────────────────
        toolbar = QHBoxLayout()
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("Search by name or service number...")
        self._search_box.setMinimumHeight(32)
        self._search_box.textChanged.connect(self._on_search)
        toolbar.addWidget(self._search_box)

        self._btn_add = QPushButton("+ Add Personnel")
        self._btn_add.setObjectName("primaryButton")
        self._btn_add.setEnabled(auth_session.is_admin())
        self._btn_add.clicked.connect(self._on_add)
        toolbar.addWidget(self._btn_add)

        self._btn_edit = QPushButton("Edit")
        self._btn_edit.setEnabled(False)
        self._btn_edit.clicked.connect(self._on_edit)
        toolbar.addWidget(self._btn_edit)

        self._btn_delete = QPushButton("Delete")
        self._btn_delete.setObjectName("dangerButton")
        self._btn_delete.setEnabled(False)
        self._btn_delete.clicked.connect(self._on_delete)
        toolbar.addWidget(self._btn_delete)

        layout.addLayout(toolbar)

        # ── Table ─────────────────────────────────────────────────────────────
        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(
            ["ID", "Service No.", "Full Name", "Rank/Designation", "Department", "Status"]
        )
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._table)

    def _load_data(self, search: str = ""):
        self._table.setRowCount(0)
        try:
            with session_scope() as session:
                query = session.query(Personnel)
                if search:
                    pat = f"%{search}%"
                    from sqlalchemy import or_
                    query = query.filter(
                        or_(
                            Personnel.full_name.ilike(pat),
                            Personnel.service_number.ilike(pat),
                        )
                    )
                persons = query.order_by(Personnel.full_name).all()
                rows = [p.to_dict() for p in persons]
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        for d in rows:
            row = self._table.rowCount()
            self._table.insertRow(row)
            for col, val in enumerate([
                str(d["id"]),
                d["service_number"],
                d["full_name"],
                d.get("rank_designation") or "",
                d.get("department") or "",
                "Active" if d["is_active"] else "Inactive",
            ]):
                item = QTableWidgetItem(val)
                item.setData(Qt.ItemDataRole.UserRole, d["id"])
                self._table.setItem(row, col, item)

    def _on_search(self, text: str):
        self._load_data(search=text.strip())

    def _on_selection_changed(self):
        selected = self._table.selectedItems()
        has_sel = len(selected) > 0
        is_admin = auth_session.is_admin()
        self._btn_edit.setEnabled(has_sel and is_admin)
        self._btn_delete.setEnabled(has_sel and is_admin)

    def _selected_id(self) -> int | None:
        rows = self._table.selectedItems()
        if not rows:
            return None
        return rows[0].data(Qt.ItemDataRole.UserRole)

    @requires_role(Role.ADMIN)
    def _on_add(self, _checked=False):
        from ui.dialogs.add_person_dialog import AddPersonDialog
        dlg = AddPersonDialog(matcher=self._matcher, parent=self)
        if dlg.exec():
            self._load_data()

    @requires_role(Role.ADMIN)
    def _on_edit(self, _checked=False):
        pid = self._selected_id()
        if pid is None:
            return
        from ui.dialogs.add_person_dialog import AddPersonDialog
        dlg = AddPersonDialog(personnel_id=pid, matcher=self._matcher, parent=self)
        if dlg.exec():
            self._load_data()

    @requires_role(Role.ADMIN)
    def _on_delete(self, _checked=False):
        pid = self._selected_id()
        if pid is None:
            return
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Delete this personnel record and all associated photos/embeddings?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            with session_scope() as session:
                person = session.get(Personnel, pid)
                if person:
                    write_audit_log("delete_personnel", "personnel", pid,
                                    {"name": person.full_name, "sn": person.service_number})
                    session.delete(person)
            if self._matcher:
                with session_scope() as session:
                    self._matcher.reload(session)
            self._load_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def on_shown(self):
        self._load_data(self._search_box.text().strip())
