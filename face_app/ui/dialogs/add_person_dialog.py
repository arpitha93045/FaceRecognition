from __future__ import annotations

import shutil
import uuid
from datetime import datetime
from pathlib import Path

import cv2
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QScrollArea, QTabWidget, QVBoxLayout, QWidget, QComboBox,
)

from db.connection import session_scope
from db.models import Department, FaceEmbedding, Personnel, Photo
from face_engine.detector import FaceDetector
from face_engine.embedder import extract_embedding
from face_engine.encryption import encrypt_embedding
from face_engine.matcher import EmbeddingMatcher
from security.auth import auth_session
from security.audit import write_audit_log
from utils.config_loader import Config


class AddPersonDialog(QDialog):
    def __init__(
        self,
        personnel_id: int | None = None,
        matcher: EmbeddingMatcher | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._pid = personnel_id
        self._matcher = matcher
        self._staged_photos: list[Path] = []
        self._existing_photos: list[dict] = []
        self._detector = FaceDetector()
        self.setWindowTitle("Edit Personnel" if personnel_id else "Add Personnel")
        self.setMinimumWidth(560)
        self._build_ui()
        if personnel_id:
            self._load_existing()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        tabs.addTab(self._build_info_tab(), "Personal Info")
        tabs.addTab(self._build_photos_tab(), "Photos / Face Data")
        layout.addWidget(tabs)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    # ── Info tab ──────────────────────────────────────────────────────────────

    def _build_info_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(10)

        self._f_service = QLineEdit()
        self._f_name    = QLineEdit()
        self._f_rank    = QLineEdit()
        self._f_email   = QLineEdit()
        self._f_phone   = QLineEdit()
        self._f_notes   = QLineEdit()
        self._f_dept    = QComboBox()
        self._f_dept.setEditable(True)
        self._f_dept.setPlaceholderText("Select or type department…")

        self._load_departments()

        form.addRow("Service Number *:", self._f_service)
        form.addRow("Full Name *:", self._f_name)
        form.addRow("Rank / Designation:", self._f_rank)
        form.addRow("Department:", self._f_dept)
        form.addRow("Email:", self._f_email)
        form.addRow("Phone:", self._f_phone)
        form.addRow("Notes:", self._f_notes)
        return w

    def _load_departments(self):
        try:
            with session_scope() as session:
                depts = session.query(Department).order_by(Department.name).all()
                names = [d.name for d in depts]
        except Exception:
            names = []
        self._f_dept.clear()
        self._f_dept.addItem("")
        for n in names:
            self._f_dept.addItem(n)

    # ── Photos tab ────────────────────────────────────────────────────────────

    def _build_photos_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)

        layout.addWidget(QLabel("Add one or more face photos. A face must be detected in each photo."))

        btn_add = QPushButton("Browse Photos…")
        btn_add.clicked.connect(self._on_browse_photos)
        layout.addWidget(btn_add)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._photo_container = QWidget()
        self._photo_layout = QHBoxLayout(self._photo_container)
        self._photo_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(self._photo_container)
        layout.addWidget(scroll)

        self._photo_status = QLabel("")
        layout.addWidget(self._photo_status)
        return w

    def _on_browse_photos(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Face Photos", "",
            "Images (*.jpg *.jpeg *.png *.bmp *.webp)"
        )
        for path in paths:
            self._add_photo_preview(path)

    def _add_photo_preview(self, path: str):
        img = cv2.imread(path)
        if img is None:
            return
        faces = self._detector.detect(img)
        if not faces:
            QMessageBox.warning(self, "No Face", f"No face detected in:\n{path}\n\nThis photo will be skipped.")
            return

        self._staged_photos.append(Path(path))
        pix = QPixmap(path).scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio)
        lbl = QLabel()
        lbl.setPixmap(pix)
        lbl.setToolTip(path)
        self._photo_layout.addWidget(lbl)
        self._photo_status.setText(f"{len(self._staged_photos)} photo(s) ready")

    # ── Load existing record ──────────────────────────────────────────────────

    def _load_existing(self):
        try:
            with session_scope() as session:
                p = session.get(Personnel, self._pid)
                if not p:
                    return
                self._f_service.setText(p.service_number)
                self._f_name.setText(p.full_name)
                self._f_rank.setText(p.rank_designation or "")
                self._f_email.setText(p.email or "")
                self._f_phone.setText(p.phone or "")
                self._f_notes.setText(p.notes or "")
                if p.department:
                    idx = self._f_dept.findText(p.department.name)
                    if idx >= 0:
                        self._f_dept.setCurrentIndex(idx)
                self._existing_photos = [ph.to_dict() for ph in p.photos]
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # ── Save ──────────────────────────────────────────────────────────────────

    def _save(self):
        service_num = self._f_service.text().strip()
        full_name   = self._f_name.text().strip()
        if not service_num or not full_name:
            QMessageBox.warning(self, "Validation", "Service Number and Full Name are required.")
            return

        dept_name = self._f_dept.currentText().strip()

        try:
            with session_scope() as session:
                # Get or create department
                dept_id = None
                if dept_name:
                    dept = session.query(Department).filter_by(name=dept_name).first()
                    if not dept:
                        dept = Department(name=dept_name)
                        session.add(dept)
                        session.flush()
                    dept_id = dept.id

                if self._pid:
                    person = session.get(Personnel, self._pid)
                    person.service_number   = service_num
                    person.full_name        = full_name
                    person.rank_designation = self._f_rank.text().strip() or None
                    person.department_id    = dept_id
                    person.email            = self._f_email.text().strip() or None
                    person.phone            = self._f_phone.text().strip() or None
                    person.notes            = self._f_notes.text().strip() or None
                    person.updated_at       = datetime.utcnow()
                    action = "edit_personnel"
                else:
                    person = Personnel(
                        service_number=service_num,
                        full_name=full_name,
                        rank_designation=self._f_rank.text().strip() or None,
                        department_id=dept_id,
                        email=self._f_email.text().strip() or None,
                        phone=self._f_phone.text().strip() or None,
                        notes=self._f_notes.text().strip() or None,
                        created_by=auth_session.user_id,
                    )
                    session.add(person)
                    action = "add_personnel"

                session.flush()
                pid = person.id

                # Process staged photos
                for src_path in self._staged_photos:
                    img = cv2.imread(str(src_path))
                    faces = self._detector.detect(img)
                    if not faces:
                        continue

                    # Copy photo to storage
                    dest_name = f"{pid}_{uuid.uuid4().hex}{src_path.suffix}"
                    dest_path = Config.photo_storage_dir / dest_name
                    shutil.copy2(src_path, dest_path)

                    photo = Photo(
                        personnel_id=pid,
                        filename=src_path.name,
                        storage_path=str(dest_path),
                        is_primary=len(person.photos) == 0,
                        uploaded_by=auth_session.user_id,
                    )
                    session.add(photo)
                    session.flush()

                    # Extract + encrypt embedding
                    face = faces[0]
                    emb_vec = extract_embedding(face)
                    emb_enc = encrypt_embedding(emb_vec)

                    fe = FaceEmbedding(
                        personnel_id=pid,
                        photo_id=photo.id,
                        embedding_enc=emb_enc,
                    )
                    session.add(fe)

                write_audit_log(action, "personnel", pid, {"name": full_name, "sn": service_num})

            # Reload matcher
            if self._matcher:
                with session_scope() as session:
                    self._matcher.reload(session)

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")
