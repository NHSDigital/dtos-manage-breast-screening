import json
import os

import pytest
from ninja.testing import TestClient

from manage_breast_screening.batches import api

client = TestClient(api.batch_api)


@pytest.mark.django_db
def test_batch_endpoint(monkeypatch):
    monkeypatch.setenv("BATCH_API_AUTH_TOKEN", "testtoken")
    monkeypatch.setenv("BATCH_API_ENABLED", "true")

    fixture_path = (
        f"{os.path.dirname(os.path.realpath(__file__))}/fixtures/bss_batch.json"
    )
    with open(fixture_path) as f:
        batch_data = json.load(f)

    response = client.post(
        "",
        json=batch_data,
        headers={"Authorization": "Bearer testtoken"},
    )

    assert response.status_code == 201
    assert response.json()["bss_batch_id"] == batch_data["bssBatchID"]


def test_batch_endpoint_invalid_batch(monkeypatch):
    monkeypatch.setenv("BATCH_API_AUTH_TOKEN", "testtoken")
    monkeypatch.setenv("BATCH_API_ENABLED", "true")

    fixture_path = (
        f"{os.path.dirname(os.path.realpath(__file__))}/fixtures/bss_batch_invalid.json"
    )
    with open(fixture_path) as f:
        batch_data = json.load(f)

    response = client.post(
        "",
        json=batch_data,
        headers={"Authorization": "Bearer testtoken"},
    )

    assert response.status_code == 422


@pytest.mark.django_db
def test_batch_endpoint_create_exception(monkeypatch):
    from unittest.mock import MagicMock

    monkeypatch.setenv("BATCH_API_AUTH_TOKEN", "testtoken")
    monkeypatch.setenv("BATCH_API_ENABLED", "true")

    fixture_path = (
        f"{os.path.dirname(os.path.realpath(__file__))}/fixtures/bss_batch.json"
    )
    with open(fixture_path) as f:
        batch_data = json.load(f)

    mock_service = MagicMock(
        side_effect=Exception("Database error"),
    )
    monkeypatch.setattr(
        "manage_breast_screening.batches.api.BatchService.create_batch_from_payload",
        mock_service,
    )

    response = client.post(
        "",
        json=batch_data,
        headers={"Authorization": "Bearer testtoken"},
    )

    assert response.status_code == 500
    response_data = response.json()
    assert response_data["title"] == "Internal Server Error"
    assert response_data["status"] == 500
    assert response_data["detail"] == "An error occurred while creating the batch"


def test_batch_endpoint_no_auth():
    response = client.post("")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Unauthorized",
    }


def test_batch_endpoint_api_disabled(monkeypatch):
    monkeypatch.setenv("BATCH_API_AUTH_TOKEN", "testtoken")
    monkeypatch.setenv("BATCH_API_ENABLED", "false")

    fixture_path = (
        f"{os.path.dirname(os.path.realpath(__file__))}/fixtures/bss_batch.json"
    )
    with open(fixture_path) as f:
        batch_data = json.load(f)

    response = client.post(
        "", json=batch_data, headers={"Authorization": "Bearer testtoken"}
    )

    assert response.status_code == 403
    assert response.json() == {"status": "API is not available"}


def test_batch_wrong_auth(monkeypatch):
    monkeypatch.setenv("BATCH_API_AUTH_TOKEN", "testtoken")
    monkeypatch.setenv("BATCH_API_ENABLED", "true")

    response = client.post(
        "",
        headers={"Authorization": "Bearer wrongtoken"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_batch_empty_expected_token(monkeypatch):
    monkeypatch.setenv("BATCH_API_AUTH_TOKEN", "")
    monkeypatch.setenv("BATCH_API_ENABLED", "true")

    response = client.post(
        "",
        headers={"Authorization": "Bearer testtoken"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_batch_empty_provided_token(monkeypatch):
    monkeypatch.setenv("BATCH_API_AUTH_TOKEN", "testtoken")
    monkeypatch.setenv("BATCH_API_ENABLED", "true")

    response = client.post(
        "",
        headers={"Authorization": "Bearer "},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_batch_no_token(monkeypatch):
    monkeypatch.delenv("BATCH_API_AUTH_TOKEN", raising=False)
    monkeypatch.setenv("BATCH_API_ENABLED", "true")

    response = client.post("")

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}
