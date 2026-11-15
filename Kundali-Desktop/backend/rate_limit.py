"""Shared rate-limiter instance.

Defined in its own module to avoid the circular import between ``main`` and
``api.endpoints`` (both need the limiter). ``main`` attaches this instance to
``app.state`` and registers the exception handler.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

from config import settings

limiter = Limiter(key_func=get_remote_address, enabled=settings.RATE_LIMIT_ENABLED)
