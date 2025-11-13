"""
Shared authentication models.
"""

from pydantic import BaseModel
from typing import List


class AuthContext(BaseModel):
    """
    Authenticated user context.
    Shared across all services for consistent authentication.
    """
    user_id: str
    tenant_id: str
    email: str
    roles: List[str]
    permissions: List[str]
    is_superuser: bool

    class Config:
        frozen = False  # Allow modifications if needed
