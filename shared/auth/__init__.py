"""
Shared authentication module for TempoNest services.
Eliminates code duplication across microservices.
"""

from .models import AuthContext
from .client import AuthClient
from .middleware import (
    get_current_user,
    require_permission,
    require_any_permission,
    set_auth_client,
    security
)

__all__ = [
    "AuthContext",
    "AuthClient",
    "get_current_user",
    "require_permission",
    "require_any_permission",
    "set_auth_client",
    "security"
]
