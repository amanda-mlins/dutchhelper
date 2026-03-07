"""
Shared rate limiter instance.

Defined in its own module to avoid circular imports between main.py and
auth_routes.py. Both modules import from here.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
