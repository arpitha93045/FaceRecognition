from __future__ import annotations

import csv
from datetime import date

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox, QDateEdit, QFileDialog, QHBoxLayout, QLabel,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QTabWidget, QVBoxLayout, QWidget, QHeaderView,
)
from PyQt6.QtCore import QDate

from db.connection import session_scope
from db.models import AttendanceLog, Personnel, UnknownDetection


class LogsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QLabel("Entry / Attendance Logs")
        header.setObjectName("pageTitle")
        layout.addWidget(header)

        tabs = QTabWidget()
        tabs.addTab(self._build_attendance_tab(), "Attendance Logs")
        tabs.addTab(self._build_unknown_tab(), "Unknown Detections")
        layout.addWidget(tabs)

    # ── Attendance tab ────────────────────────────────────────────────────────

    def _build_attendance_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)

        filt = QHBoxLayout()
        filt.addWidget(QLabel("From:"))
        self._att_from = QDateEdit(QDate.currentDate())
        self._att_from.setCalendarPopup(True)
        filt.addWidget(self._att_from)
        filt.addWidget(QLabel("To:"))
        self._att_to = QDateEdit(QDate.currentDate())
        self._att_to.setCalendarPopup(True)
        filt.addWidget(self._att_to)

        btn_search = QPushButton("Search")
        btn_search.clicked.connect(self._load_attendance)
        filt.addWidget(btn_search)

        btn_export = QPushButton("Export CSV")
        btn_export.clicked.connect(lambda: self._export_csv("attendance"))
        filt.addWidget(btn_export)
        filt.addStretch()
        layout.addLayout(filt)

        self._att_table = QTableWidget(0, 6)
        self._att_table.setHorizontalHeaderLabels(
            ["ID", "Name", "Service No.", "Event", "Camera", "Time"]
        )
        self._att_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._att_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._att_table.setAlternatingRowColors(True)
        layout.addWidget(self._att_table)
        return w

    def _load_attendance(self):
        from_dt = self._att_from.date().toPyDate()
        to_dt   = self._att_to.date().toPyDate()
        try:
            with session_scope() as session:
                from sqlalchemy import cast
                from sqlalchemy import Date as SADate
                rows = [
                    (
                        str(log.id),
                        person.full_name,
                        person.service_number,
                        log.event_type.upper(),
                        str(log.camera_id or ""),
                        log.logged_at.strftime("%Y-%m-%d %H:%M:%S") if log.logged_at else "",
                    )
                    for log, person in (
                        session.query(AttendanceLog, Personnel)
                        .join(Personnel, AttendanceLog.personnel_id == Personnel.id)
                        .filter(cast(AttendanceLog.logged_at, SADate) >= from_dt)
                        .filter(cast(AttendanceLog.logged_at, SADate) <= to_dt)
                        .order_by(AttendanceLog.logged_at.desc())
                        .limit(500)
                        .all()
                    )
                ]
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        self._att_table.setRowCount(0)
        self._att_rows = []
        for r in rows:
            self._att_rows.append(r)
            row = self._att_table.rowCount()
            self._att_table.insertRow(row)
            for col, val in enumerate(r):
                self._att_table.setItem(row, col, QTableWidgetItem(val))

    # ── Unknown tab ───────────────────────────────────────────────────────────

    def _build_unknown_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)

        filt = QHBoxLayout()
        filt.addWidget(QLabel("From:"))
        self._unk_from = QDateEdit(QDate.currentDate())
        self._unk_from.setCalendarPopup(True)
        filt.addWidget(self._unk_from)
        filt.addWidget(QLabel("To:"))
        self._unk_to = QDateEdit(QDate.currentDate())
        self._unk_to.setCalendarPopup(True)
        filt.addWidget(self._unk_to)

        btn_search = QPushButton("Search")
        btn_search.clicked.connect(self._load_unknown)
        filt.addWidget(btn_search)

        btn_export = QPushButton("Export CSV")
        btn_export.clicked.connect(lambda: self._export_csv("unknown"))
        filt.addWidget(btn_export)
        filt.addStretch()
        layout.addLayout(filt)

        self._unk_table = QTableWidget(0, 5)
        self._unk_table.setHorizontalHeaderLabels(
            ["ID", "Camera", "Best Score", "Resolved", "Detected At"]
        )
        self._unk_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._unk_table.setAlternatingRowColors(True)
        layout.addWidget(self._unk_table)
        return w

    def _load_unknown(self):
        from_dt = self._unk_from.date().toPyDate()
        to_dt   = self._unk_to.date().toPyDate()
        try:
            with session_scope() as session:
                from sqlalchemy import cast
                from sqlalchemy import Date as SADate
                rows = (
                    session.query(UnknownDetection)
                    .filter(cast(UnknownDetection.detected_at, SADate) >= from_dt)
                    .filter(cast(UnknownDetection.detected_at, SADate) <= to_dt)
                    .order_by(UnknownDetection.detected_at.desc())
                    .limit(500)
                    .all()
                )
                data = [r.to_dict() for r in rows]
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        self._unk_table.setRowCount(0)
        self._unk_rows = []
        for d in data:
            r = [
                str(d["id"]),
                str(d["camera_id"] or ""),
                f"{d['best_score']:.2%}" if d["best_score"] is not None else "",
                "Yes" if d["resolved"] else "No",
                d["detected_at"] or "",
            ]
            self._unk_rows.append(r)
            row = self._unk_table.rowCount()
            self._unk_table.insertRow(row)
            for col, val in enumerate(r):
                self._unk_table.setItem(row, col, QTableWidgetItem(val))

    def _export_csv(self, which: str):
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        rows = getattr(self, f"_{which}_rows", [])
        try:
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(rows)
            QMessageBox.information(self, "Export", f"Exported {len(rows)} rows.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def on_shown(self):
        self._load_attendance()
        self._load_unknown()
