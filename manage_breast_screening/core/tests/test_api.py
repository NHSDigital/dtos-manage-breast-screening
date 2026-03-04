import hmac
import os
from unittest.mock import patch

from ninja.testing import TestClient

from manage_breast_screening.core.api import GlobalAuth, api

os.environ["NINJA_SKIP_REGISTRY"] = "yes"

client = TestClient(api)


def test_status_endpoint(monkeypatch):
    monkeypatch.setenv("API_AUTH_TOKEN", "testtoken")
    monkeypatch.setenv("API_ENABLED", "true")

    response = client.get("/status", headers={"Authorization": "Bearer testtoken"})

    assert response.status_code == 200
    assert response.json() == {"status": "API is available"}


def test_status_endpoint_no_auth():
    response = client.get("/status")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Unauthorized",
    }


def test_status_endpoint_api_disabled(monkeypatch):
    monkeypatch.setenv("API_AUTH_TOKEN", "testtoken")
    monkeypatch.setenv("API_ENABLED", "false")

    response = client.get("/status", headers={"Authorization": "Bearer testtoken"})

    assert response.status_code == 403
    assert response.json() == {"status": "API is not available"}


def test_status_wrong_auth(monkeypatch):
    monkeypatch.setenv("API_AUTH_TOKEN", "testtoken")
    monkeypatch.setenv("API_ENABLED", "true")

    response = client.get(
        "/status",
        headers={"Authorization": "Bearer wrongtoken"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_status_empty_expected_token(monkeypatch):
    monkeypatch.setenv("API_AUTH_TOKEN", "")
    monkeypatch.setenv("API_ENABLED", "true")

    response = client.get(
        "/status",
        headers={"Authorization": "Bearer testtoken"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_status_empty_provided_token(monkeypatch):
    monkeypatch.setenv("API_AUTH_TOKEN", "testtoken")
    monkeypatch.setenv("API_ENABLED", "true")

    response = client.get(
        "/status",
        headers={"Authorization": "Bearer "},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_status_no_token(monkeypatch):
    monkeypatch.delenv("API_AUTH_TOKEN", raising=False)
    monkeypatch.setenv("API_ENABLED", "true")

    response = client.get("/status")

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_hmac_compare_digest_true(monkeypatch):
    monkeypatch.setenv("API_AUTH_TOKEN", "expected-token")
    auth = GlobalAuth()

    with patch.object(hmac, "compare_digest", return_value=True) as mock_compare:
        result = auth.authenticate(object(), "provided-token")

    mock_compare.assert_called_once_with("provided-token", "expected-token")
    assert result == "provided-token"


def test_hmac_compare_digest_false(monkeypatch):
    monkeypatch.setenv("API_AUTH_TOKEN", "expected-token")
    auth = GlobalAuth()

    with patch.object(hmac, "compare_digest", return_value=False) as mock_compare:
        result = auth.authenticate(object(), "provided-token")

    mock_compare.assert_called_once_with("provided-token", "expected-token")
    assert not result


def test_api_docs(monkeypatch):
    monkeypatch.setenv("API_DOCS_ENABLED", "true")

    response = client.get("/docs")

    assert response.status_code == 200
    assert "Manage Breast Screening API" in response.content.decode()


def test_api_docs_disabled(monkeypatch):
    monkeypatch.setenv("API_DOCS_ENABLED", "false")

    response = client.get("/docs")

    assert response.status_code == 404
    assert "API documentation is not available" in response.content.decode()
