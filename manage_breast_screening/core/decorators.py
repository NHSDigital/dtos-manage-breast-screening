import functools
from typing import Callable


def basic_auth_exempt(view_func: Callable) -> Callable:
    """Mark a view function as exempt from BasicAuthMiddleware.

    This sets an attribute on both the original view and the wrapped function so
    the middleware can detect the exemption regardless of decorator ordering.
    """

    setattr(view_func, "basic_auth_exempt", True)

    @functools.wraps(view_func)
    def _wrapped(*args, **kwargs):
        return view_func(*args, **kwargs)

    setattr(_wrapped, "basic_auth_exempt", True)
    return _wrapped
