from typing import Callable

_basic_auth_exempt_views = set()
_current_provider_exempt_views = set()


def basic_auth_exempt(view_func: Callable) -> Callable:
    """Mark a view function as exempt from BasicAuthMiddleware.

    Uses a registry approach that is decorator-order independent.
    """
    _basic_auth_exempt_views.add(view_func_identifier(view_func))
    return view_func


def is_basic_auth_exempt(view_func: Callable) -> bool:
    """Check if a view function is exempt from BasicAuthMiddleware."""
    return view_func_identifier(view_func) in _basic_auth_exempt_views


def current_provider_exempt(view_func: Callable) -> Callable:
    """Mark a view function as exempt from CurrentProviderMiddleware.

    Uses a registry approach that is decorator-order independent.
    """
    _current_provider_exempt_views.add(view_func_identifier(view_func))
    return view_func


def is_current_provider_exempt(view_func: Callable) -> bool:
    """Check if a view function is exempt from CurrentProviderMiddleware."""
    return view_func_identifier(view_func) in _current_provider_exempt_views


def view_func_identifier(view_func: Callable) -> str:
    return f"{view_func.__module__}.{view_func.__qualname__}"
