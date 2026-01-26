import os

from ninja.testing import TestClient

from manage_breast_screening.core.api import api

os.environ["NINJA_SKIP_REGISTRY"] = "yes"

client = TestClient(api)


def test_status_endpoint(monkeypatch):
    monkeypatch.setenv("API_ENABLED", "true")

    response = client.get("/status")

    assert response.status_code == 200
    assert response.json() == {"status": "API is available"}


def test_status_endpoint_api_disabled(monkeypatch):
    monkeypatch.setenv("API_ENABLED", "false")

    response = client.get("/status")

    assert response.status_code == 403
    assert response.json() == {"status": "API is not available"}
