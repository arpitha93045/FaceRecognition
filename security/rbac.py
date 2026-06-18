from __future__ import annotations

import functools
from enum import Enum

from PyQt6.QtWidgets import QMessageBox


class Role(str, Enum):
    ADMIN    = "admin"
    OPERATOR = "operator"


def requires_role(*roles: Role):
    """Decorator for PyQt6 slot methods — shows error dialog if role insufficient."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            from security.auth import auth_session
            if not auth_session.is_authenticated():
                QMessageBox.warning(None, "Access Denied", "You are not logged in.")
                return
            if auth_session.role not in [r.value for r in roles]:
                QMessageBox.warning(
                    None, "Access Denied",
                    f"This action requires one of: {', '.join(r.value for r in roles)}."
                )
                return
            return func(self, *args, **kwargs)
        return wrapper
    return decorator
