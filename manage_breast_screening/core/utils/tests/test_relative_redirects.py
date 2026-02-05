import pytest
from django.test import RequestFactory

from manage_breast_screening.core.utils.relative_redirects import (
    extract_relative_redirect_url,
)


@pytest.mark.parametrize(
    "return_url,expected",
    [
        ("/internal-path", "/internal-path"),
        ("/internal/path", "/internal/path"),
        ("/internal/path/", "/internal/path/"),
        ("/internal/path/?x=1&y=Abc+xyz%21&c=", "/internal/path/?x=1&y=Abc+xyz%21&c="),
        ("/internal path/", "/internal%20path/"),
        ("internal", "/default"),
        ("internal/path", "/default"),
        ("./internal", "/default"),
        ("../internal", "/default"),
        ("../../internal", "/default"),
        ("https://evil.com", "/default"),
        ("https://evil.com/login", "/default"),
        ("//evil.com", "/default"),
        ("///evil.com", "/default"),
        ("////evil.com", "/default"),
        ("", "/default"),
        (None, "/default"),
    ],
)
def test_extract_relative_redirect_url(return_url, expected):
    factory = RequestFactory()
    parameters = {"return_url": return_url} if return_url else {}
    assert (
        extract_relative_redirect_url(factory.get("/", parameters), "/default")
        == expected
    )
    assert (
        extract_relative_redirect_url(factory.post("/", parameters), "/default")
        == expected
    )


def test_extract_relative_redirect_url_with_alternative_parameter_name_and_valid_value():
    """
    extract_relative_redirect_url correctly retrieves the URL when using a custom parameter name.
    """
    factory = RequestFactory()
    parameters = {"abc": "/valid-return-url"}
    assert (
        extract_relative_redirect_url(
            factory.get("/", parameters), default="/default", parameter_name="abc"
        )
        == "/valid-return-url"
    )
    assert (
        extract_relative_redirect_url(
            factory.post("/", parameters), default="/default", parameter_name="abc"
        )
        == "/valid-return-url"
    )


def test_extract_relative_redirect_url_with_alternative_parameter_name_and_invalid_value():
    """
    extract_relative_redirect_url uses the default value when using a custom parameter name and an invalid URL.
    """
    factory = RequestFactory()
    parameters = {"abc": "invalid-return-url"}
    assert (
        extract_relative_redirect_url(
            factory.get("/", parameters), default="/default", parameter_name="abc"
        )
        == "/default"
    )
    assert (
        extract_relative_redirect_url(
            factory.post("/", parameters), default="/default", parameter_name="abc"
        )
        == "/default"
    )


def test_extract_relative_redirect_url_without_specifying_default():
    """
    If no default value is specified, extract_relative_redirect_url returns None for an invalid URL.
    """
    factory = RequestFactory()
    parameters = {"return_url": "invalid-return-url"}
    assert not extract_relative_redirect_url(factory.get("/", parameters))
