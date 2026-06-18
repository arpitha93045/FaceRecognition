from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, BigInteger, Column, DateTime, ForeignKey, Index,
    Integer, LargeBinary, Numeric, String, Text, JSON,
)
from sqlalchemy.orm import relationship

from db.connection import Base


class Role(Base):
    __tablename__ = "roles"

    id          = Column(Integer, primary_key=True)
    name        = Column(String(50), unique=True, nullable=False)
    description = Column(Text)

    users = relationship("User", back_populates="role")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "description": self.description}


class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True)
    username      = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name     = Column(String(255))
    role_id       = Column(Integer, ForeignKey("roles.id"), nullable=False)
    is_active     = Column(Boolean, nullable=False, default=True)
    created_at    = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    last_login    = Column(DateTime(timezone=True))

    role = relationship("Role", back_populates="users")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "role": self.role.name if self.role else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }


class Department(Base):
    __tablename__ = "departments"

    id   = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)

    personnel = relationship("Personnel", back_populates="department")

    def to_dict(self):
        return {"id": self.id, "name": self.name}


class Personnel(Base):
    __tablename__ = "personnel"

    id               = Column(Integer, primary_key=True)
    service_number   = Column(String(100), unique=True, nullable=False)
    full_name        = Column(String(255), nullable=False)
    rank_designation = Column(String(100))
    department_id    = Column(Integer, ForeignKey("departments.id"))
    email            = Column(String(255))
    phone            = Column(String(50))
    notes            = Column(Text)
    is_active        = Column(Boolean, nullable=False, default=True)
    created_at       = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at       = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    created_by       = Column(Integer, ForeignKey("users.id"))

    department       = relationship("Department", back_populates="personnel")
    photos           = relationship("Photo", back_populates="personnel", cascade="all, delete-orphan")
    embeddings       = relationship("FaceEmbedding", back_populates="personnel", cascade="all, delete-orphan")
    attendance_logs  = relationship("AttendanceLog", back_populates="personnel")

    __table_args__ = (
        Index("idx_personnel_service_number", "service_number"),
        Index("idx_personnel_full_name", "full_name"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "service_number": self.service_number,
            "full_name": self.full_name,
            "rank_designation": self.rank_designation,
            "department": self.department.name if self.department else None,
            "department_id": self.department_id,
            "email": self.email,
            "phone": self.phone,
            "notes": self.notes,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Photo(Base):
    __tablename__ = "photos"

    id           = Column(Integer, primary_key=True)
    personnel_id = Column(Integer, ForeignKey("personnel.id", ondelete="CASCADE"), nullable=False)
    filename     = Column(String(500), nullable=False)
    storage_path = Column(String(1000), nullable=False)
    is_primary   = Column(Boolean, nullable=False, default=False)
    uploaded_at  = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    uploaded_by  = Column(Integer, ForeignKey("users.id"))

    personnel  = relationship("Personnel", back_populates="photos")
    embeddings = relationship("FaceEmbedding", back_populates="photo")

    def to_dict(self):
        return {
            "id": self.id,
            "personnel_id": self.personnel_id,
            "filename": self.filename,
            "storage_path": self.storage_path,
            "is_primary": self.is_primary,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
        }


class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"

    id            = Column(Integer, primary_key=True)
    personnel_id  = Column(Integer, ForeignKey("personnel.id", ondelete="CASCADE"), nullable=False)
    photo_id      = Column(Integer, ForeignKey("photos.id", ondelete="SET NULL"))
    embedding_enc = Column(LargeBinary, nullable=False)
    model_version = Column(String(100), nullable=False, default="buffalo_l")
    created_at    = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    personnel = relationship("Personnel", back_populates="embeddings")
    photo     = relationship("Photo", back_populates="embeddings")

    __table_args__ = (
        Index("idx_embeddings_personnel", "personnel_id"),
    )


class Camera(Base):
    __tablename__ = "cameras"

    id           = Column(Integer, primary_key=True)
    name         = Column(String(255), nullable=False)
    location     = Column(String(500))
    source_type  = Column(String(20), nullable=False, default="webcam")
    source_uri   = Column(String(1000))
    device_index = Column(Integer)
    is_active    = Column(Boolean, nullable=False, default=True)
    added_at     = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "source_type": self.source_type,
            "source_uri": self.source_uri,
            "device_index": self.device_index,
            "is_active": self.is_active,
        }


class AttendanceLog(Base):
    __tablename__ = "attendance_logs"

    id            = Column(BigInteger, primary_key=True)
    personnel_id  = Column(Integer, ForeignKey("personnel.id"), nullable=False)
    camera_id     = Column(Integer, ForeignKey("cameras.id"))
    event_type    = Column(String(20), nullable=False, default="entry")
    confidence    = Column(Numeric(5, 4))
    snapshot_path = Column(String(1000))
    logged_at     = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    personnel = relationship("Personnel", back_populates="attendance_logs")

    __table_args__ = (
        Index("idx_attendance_personnel", "personnel_id"),
        Index("idx_attendance_logged_at", "logged_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "personnel_id": self.personnel_id,
            "name": self.personnel.full_name if self.personnel else "Unknown",
            "service_number": self.personnel.service_number if self.personnel else "",
            "camera_id": self.camera_id,
            "event_type": self.event_type,
            "confidence": float(self.confidence) if self.confidence is not None else None,
            "snapshot_path": self.snapshot_path,
            "logged_at": self.logged_at.isoformat() if self.logged_at else None,
        }


class UnknownDetection(Base):
    __tablename__ = "unknown_detections"

    id            = Column(BigInteger, primary_key=True)
    camera_id     = Column(Integer, ForeignKey("cameras.id"))
    snapshot_path = Column(String(1000))
    best_score    = Column(Numeric(5, 4))
    resolved      = Column(Boolean, nullable=False, default=False)
    resolved_by   = Column(Integer, ForeignKey("users.id"))
    resolved_at   = Column(DateTime(timezone=True))
    notes         = Column(Text)
    detected_at   = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_unknown_detected_at", "detected_at"),
        Index("idx_unknown_resolved", "resolved"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "camera_id": self.camera_id,
            "snapshot_path": self.snapshot_path,
            "best_score": float(self.best_score) if self.best_score is not None else None,
            "resolved": self.resolved,
            "notes": self.notes,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
        }


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id          = Column(BigInteger, primary_key=True)
    user_id     = Column(Integer, ForeignKey("users.id"))
    username    = Column(String(100))
    action      = Column(String(255), nullable=False)
    entity_type = Column(String(100))
    entity_id   = Column(Integer)
    detail      = Column(JSON)
    ip_address  = Column(String(45))
    logged_at   = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_logged_at", "logged_at"),
        Index("idx_audit_action", "action"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "detail": self.detail,
            "logged_at": self.logged_at.isoformat() if self.logged_at else None,
        }
