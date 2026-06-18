from __future__ import annotations

from typing import Any

from db.connection import session_scope
from db.models import AuditLog


def write_audit_log(
    action: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    detail: dict[str, Any] | None = None,
) -> None:
    try:
        from security.auth import auth_session
        user_id = auth_session.user_id
        username = auth_session.username
    except Exception:
        user_id = None
        username = "system"

    try:
        with session_scope() as session:
            log = AuditLog(
                user_id=user_id,
                username=username,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                detail=detail,
            )
            session.add(log)
    except Exception as e:
        print(f"[AUDIT] Failed to write audit log: {e}")
