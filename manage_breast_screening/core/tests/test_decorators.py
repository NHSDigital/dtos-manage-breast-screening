from functools import wraps

from manage_breast_screening.core.decorators import (
    _basic_auth_exempt_views,
    basic_auth_exempt,
    is_basic_auth_exempt,
    view_func_identifier,
)


class TestBasicAuthExempt:
    def setup_method(self):
        """Clear the registry before each test."""
        _basic_auth_exempt_views.clear()

    def test_decorator_adds_view_to_registry(self):
        def view_func():
            pass

        basic_auth_exempt(view_func)

        assert is_basic_auth_exempt(view_func)
        assert view_func_identifier(view_func) in _basic_auth_exempt_views

    def test_multiple_decorations_maintain_unique_set(self):
        def view_func():
            pass

        # Decorate the same function multiple times
        basic_auth_exempt(view_func)
        basic_auth_exempt(view_func)
        basic_auth_exempt(view_func)

        # Should only appear once in the registry
        assert len(_basic_auth_exempt_views) == 1
        assert view_func_identifier(view_func) in _basic_auth_exempt_views
        assert is_basic_auth_exempt(view_func)

    def test_different_views_are_tracked_separately(self):
        def view1():
            pass

        def view2():
            pass

        basic_auth_exempt(view1)
        basic_auth_exempt(view2)

        assert len(_basic_auth_exempt_views) == 2
        assert is_basic_auth_exempt(view1)
        assert is_basic_auth_exempt(view2)

    def test_non_exempt_view_returns_false(self):
        def view_func():
            pass

        assert not is_basic_auth_exempt(view_func)
        assert view_func_identifier(view_func) not in _basic_auth_exempt_views

    def test_decorator_order_independence(self):
        def other_decorator(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        def view_func():
            pass

        # Apply decorators in different orders
        decorated1 = basic_auth_exempt(other_decorator(view_func))
        decorated2 = other_decorator(basic_auth_exempt(view_func))

        # Original function should be in registry regardless of order
        assert is_basic_auth_exempt(view_func)
        assert view_func_identifier(view_func) in _basic_auth_exempt_views

        # Decorated functions should work the same way
        assert decorated1 is not view_func  # other_decorator wraps it
        assert decorated2 is not view_func  # other_decorator wraps it

    def test_functools_wraps_interoperability(self):
        def functools_decorator(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wraps(func)(wrapper)

        @functools_decorator
        @basic_auth_exempt
        @functools_decorator
        def view_func():
            pass

        assert is_basic_auth_exempt(view_func)
        assert view_func_identifier(view_func) in _basic_auth_exempt_views

    def test_view_func_identifier(self):
        def view_func():
            pass

        assert (
            view_func_identifier(view_func)
            == f"{view_func.__module__}.{view_func.__qualname__}"
        )
