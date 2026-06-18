from __future__ import annotations

from datetime import date

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from db.connection import session_scope
from db.models import AttendanceLog, Personnel, UnknownDetection


def _stat_card(title: str, value: str, color: str) -> QFrame:
    card = QFrame()
    card.setObjectName("statCard")
    card.setStyleSheet(f"QFrame#statCard {{ border-left: 4px solid {color}; }}")
    layout = QVBoxLayout(card)
    val_lbl = QLabel(value)
    val_lbl.setObjectName("statValue")
    f = QFont()
    f.setPointSize(28)
    f.setBold(True)
    val_lbl.setFont(f)
    ttl_lbl = QLabel(title)
    ttl_lbl.setObjectName("statTitle")
    layout.addWidget(val_lbl)
    layout.addWidget(ttl_lbl)
    return card, val_lbl


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._refresh()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(30_000)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        header = QLabel("Dashboard")
        header.setObjectName("pageTitle")
        layout.addWidget(header)

        grid = QGridLayout()
        grid.setSpacing(16)

        card1, self._lbl_total    = _stat_card("Total Registered Personnel", "0", "#2196F3")
        card2, self._lbl_today    = _stat_card("Today's Entries",             "0", "#4CAF50")
        card3, self._lbl_unknown  = _stat_card("Unknown Detections Today",    "0", "#F44336")
        card4, self._lbl_cameras  = _stat_card("Active Cameras",              "0", "#FF9800")

        grid.addWidget(card1, 0, 0)
        grid.addWidget(card2, 0, 1)
        grid.addWidget(card3, 0, 2)
        grid.addWidget(card4, 0, 3)
        layout.addLayout(grid)

        recent_lbl = QLabel("Recent Activity")
        recent_lbl.setObjectName("sectionTitle")
        layout.addWidget(recent_lbl)

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["Name", "Service No.", "Event", "Camera", "Time"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table)

    def _refresh(self):
        today = date.today()
        try:
            with session_scope() as session:
                from sqlalchemy import func, cast
                from sqlalchemy import Date as SADate
                total = session.query(Personnel).filter_by(is_active=True).count()
                today_count = (
                    session.query(func.count(AttendanceLog.id))
                    .filter(cast(AttendanceLog.logged_at, SADate) == today)
                    .scalar() or 0
                )
                unknown_count = (
                    session.query(func.count(UnknownDetection.id))
                    .filter(cast(UnknownDetection.detected_at, SADate) == today)
                    .scalar() or 0
                )
                from db.models import Camera
                cam_count = session.query(Camera).filter_by(is_active=True).count()

                recent_rows = [
                    (
                        person.full_name,
                        person.service_number,
                        log.event_type.upper(),
                        str(log.camera_id or ""),
                        log.logged_at.strftime("%Y-%m-%d %H:%M:%S") if log.logged_at else "",
                    )
                    for log, person in (
                        session.query(AttendanceLog, Personnel)
                        .join(Personnel, AttendanceLog.personnel_id == Personnel.id)
                        .order_by(AttendanceLog.logged_at.desc())
                        .limit(20)
                        .all()
                    )
                ]
        except Exception as e:
            print(f"[Dashboard] DB error: {e}")
            return

        self._lbl_total.setText(str(total))
        self._lbl_today.setText(str(today_count))
        self._lbl_unknown.setText(str(unknown_count))
        self._lbl_cameras.setText(str(cam_count))

        self._table.setRowCount(0)
        for full_name, service_number, event_type, camera_id, ts in recent_rows:
            row = self._table.rowCount()
            self._table.insertRow(row)
            for col, val in enumerate([full_name, service_number, event_type, camera_id, ts]):
                self._table.setItem(row, col, QTableWidgetItem(val))

    def on_shown(self):
        self._refresh()
