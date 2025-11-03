"""
Rate limiter instance shared across the application.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from app.settings import settings


# Shared rate limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL,
    default_limits=[settings.RATE_LIMIT_AUTHENTICATED]
)
