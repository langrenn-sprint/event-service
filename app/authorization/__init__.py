"""Authorization module initialization."""

from .authorization import (
    Role,
    RoleChecker,
    TokenError,
    TokenMissingError,
    TokenValidationError,
    document_roles,
    require_roles,
)

__all__ = [
    "Role",
    "RoleChecker",
    "TokenError",
    "TokenMissingError",
    "TokenValidationError",
    "document_roles",
    "get_current_token",
    "require_roles",
]
