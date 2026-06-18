from __future__ import annotations

from datetime import datetime
from typing import Optional

import bcrypt

from db.connection import session_scope
from db.models import User, AuditLog


class AuthSession:
    def __init__(self):
        self.current_user: Optional[User] = None
        self._role_name: Optional[str] = None

    def login(self, username: str, password: str) -> bool:
        with session_scope() as session:
            user = session.query(User).filter_by(username=username, is_active=True).first()
            if user is None:
                return False

            if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
                return False

            user.last_login = datetime.utcnow()

            role_name = user.role.name if user.role else "operator"
            user_id = user.id
            full_name = user.full_name

            log = AuditLog(
                user_id=user_id,
                username=username,
                action="login",
            )
            session.add(log)
            session.commit()

            self._role_name = role_name
            self._user_id = user_id
            self._username = username
            self._full_name = full_name
            return True

    def logout(self) -> None:
        if self._username:
            try:
                with session_scope() as session:
                    log = AuditLog(
                        user_id=getattr(self, "_user_id", None),
                        username=self._username,
                        action="logout",
                    )
                    session.add(log)
            except Exception:
                pass
        self.current_user = None
        self._role_name = None
        self._user_id = None
        self._username = None
        self._full_name = None

    @property
    def role(self) -> Optional[str]:
        return self._role_name

    @property
    def username(self) -> Optional[str]:
        return getattr(self, "_username", None)

    @property
    def full_name(self) -> Optional[str]:
        return getattr(self, "_full_name", None)

    @property
    def user_id(self) -> Optional[int]:
        return getattr(self, "_user_id", None)

    def is_authenticated(self) -> bool:
        return self._role_name is not None

    def is_admin(self) -> bool:
        return self._role_name == "admin"

    def hash_password(self, plain: str) -> str:
        return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(12)).decode()

    def change_password(self, user_id: int, new_plain: str) -> None:
        new_hash = self.hash_password(new_plain)
        with session_scope() as session:
            user = session.get(User, user_id)
            if user:
                user.password_hash = new_hash


auth_session = AuthSession()
