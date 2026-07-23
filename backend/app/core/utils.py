"""
Shared utility functions used across API routes and Celery tasks.
"""
from typing import Any


def user_display_name(user: Any) -> str:
    """Returns a human-readable name for a user object."""
    first = getattr(user, "first_name", None) or ""
    last = getattr(user, "last_name", None) or ""
    full = f"{first} {last}".strip()
    return full or str(getattr(user, "email", "Unknown"))

def get_client_ip(request: Any) -> str:
    """Extracts the real client IP address from the request headers or client host."""
    if not request:
        return "127.0.0.1"
    
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
        
    return request.client.host if request.client else "127.0.0.1"
