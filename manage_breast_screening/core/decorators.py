from typing import Callable

_basic_auth_exempt_views = set()


def basic_auth_exempt(view_func: Callable) -> Callable:
    """Mark a view function as exempt from BasicAuthMiddleware.

    Uses a registry approach that is decorator-order independent.
    """
    _basic_auth_exempt_views.add(view_func)
    return view_func


def is_basic_auth_exempt(view_func: Callable) -> bool:
    """Check if a view function is exempt from BasicAuthMiddleware."""
    return view_func in _basic_auth_exempt_views
