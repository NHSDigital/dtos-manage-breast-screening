import io
import os
from unittest.mock import MagicMock, patch

import pydicom
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from ninja.testing import TestClient

from manage_breast_screening.core.api import api
from manage_breast_screening.dicom.dicom_recorder import DicomRecorder
from manage_breast_screening.dicom.models import Study
from manage_breast_screening.gateway.models import GatewayActionStatus
from manage_breast_screening.gateway.tests.factories import GatewayActionFactory

os.environ["NINJA_SKIP_REGISTRY"] = "yes"

client = TestClient(api)


@pytest.fixture
def dicom_file(dataset) -> bytes:
    with io.BytesIO() as buffer:
        pydicom.dcmwrite(buffer, dataset, enforce_file_format=True)
        buffer.seek(0)
        return SimpleUploadedFile(
            "temp.dcm", buffer.read(), content_type="application/dicom"
        )


@pytest.mark.django_db
def test_upload_success(dataset, dicom_file, monkeypatch):
    monkeypatch.setenv("API_ENABLED", "true")
    monkeypatch.setenv("API_AUTH_TOKEN", "testtoken")

    with patch.object(DicomRecorder, "appointment_in_progress", return_value=True):
        response = client.put(
            "/dicom/abc123",
            FILES={"file": dicom_file},
            headers={"Authorization": "Bearer " + os.getenv("API_AUTH_TOKEN", "")},
        )

        assert response.status_code == 201
        assert response.json() == {
            "study_instance_uid": dataset.StudyInstanceUID,
            "series_instance_uid": dataset.SeriesInstanceUID,
            "sop_instance_uid": dataset.SOPInstanceUID,
            "instance_id": 1,
        }
        assert Study.objects.last().source_message_id == "abc123"


def test_upload_no_file(monkeypatch):
    monkeypatch.setenv("API_ENABLED", "true")
    monkeypatch.setenv("API_AUTH_TOKEN", "testtoken")

    response = client.put(
        "/dicom/abc123",
        FILES={"file": None},
        headers={"Authorization": "Bearer " + os.getenv("API_AUTH_TOKEN", "")},
    )

    assert response.status_code == 422


def test_upload_invalid_file(monkeypatch):
    monkeypatch.setenv("API_ENABLED", "true")
    monkeypatch.setenv("API_AUTH_TOKEN", "testtoken")

    invalid_file = SimpleUploadedFile(
        "invalid.dcm", b"not a dicom file", content_type="application/dicom"
    )

    with patch.object(DicomRecorder, "appointment_in_progress", return_value=True):
        response = client.put(
            "/dicom/abc123",
            FILES={"file": invalid_file},
            headers={"Authorization": "Bearer " + os.getenv("API_AUTH_TOKEN", "")},
        )

    assert response.status_code == 400
    assert response.json()["title"] == "Invalid DICOM file"
    assert response.json()["status"] == 400
    assert response.json()["detail"] == "The uploaded file is not a valid DICOM file."


def test_upload_file_thats_too_large(monkeypatch):
    monkeypatch.setenv("API_ENABLED", "true")
    monkeypatch.setenv("API_AUTH_TOKEN", "testtoken")

    invalid_file = MagicMock(spec=SimpleUploadedFile, size=101 * 1024 * 1024)

    response = client.put(
        "/dicom/abc123",
        FILES={"file": invalid_file},
        headers={"Authorization": "Bearer " + os.getenv("API_AUTH_TOKEN", "")},
    )

    assert response.status_code == 400
    assert response.json()["title"] == "File too large"
    assert response.json()["status"] == 400
    assert response.json()["detail"] == "The file cannot be larger than 100MB"


def test_upload_missing_uids(dataset, monkeypatch):
    monkeypatch.setenv("API_ENABLED", "true")
    monkeypatch.setenv("API_AUTH_TOKEN", "testtoken")

    del dataset.StudyInstanceUID
    del dataset.SeriesInstanceUID
    del dataset.SOPInstanceUID

    with io.BytesIO() as buffer:
        pydicom.dcmwrite(buffer, dataset, enforce_file_format=True)
        buffer.seek(0)
        dicom_file = SimpleUploadedFile(
            "temp.dcm", buffer.read(), content_type="application/dicom"
        )

    with patch.object(DicomRecorder, "appointment_in_progress", return_value=True):
        response = client.put(
            "/dicom/abc123",
            FILES={"file": dicom_file},
            headers={"Authorization": "Bearer " + os.getenv("API_AUTH_TOKEN", "")},
        )

    assert response.status_code == 400
    assert response.json()["title"] == "Missing DICOM attributes"
    assert response.json()["status"] == 400
    assert (
        response.json()["detail"]
        == "The DICOM file is missing required UID attributes."
    )


def test_upload_appointment_not_in_progress(dicom_file, monkeypatch):
    monkeypatch.setenv("API_ENABLED", "true")
    monkeypatch.setenv("API_AUTH_TOKEN", "testtoken")

    with patch.object(DicomRecorder, "appointment_in_progress", return_value=False):
        response = client.put(
            "/dicom/abc123",
            FILES={"file": dicom_file},
            headers={"Authorization": "Bearer " + os.getenv("API_AUTH_TOKEN", "")},
        )

        assert response.status_code == 500
        assert response.json()["title"] == "Internal Server Error"


@pytest.mark.django_db
def test_upload_when_api_disabled(dicom_file, monkeypatch):
    monkeypatch.setenv("API_ENABLED", "false")
    monkeypatch.setenv("API_AUTH_TOKEN", "testtoken")

    response = client.put(
        "/dicom/abc123",
        FILES={"file": dicom_file},
        headers={"Authorization": "Bearer " + os.getenv("API_AUTH_TOKEN", "")},
    )

    assert response.status_code == 403
    assert response.json()["status"] == "API is not available"


@pytest.mark.django_db
def test_upload_no_auth(dicom_file):
    response = client.put(
        "/dicom/abc123",
        FILES={"file": dicom_file},
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Unauthorized",
    }


@pytest.mark.django_db
def test_report_failure(monkeypatch):
    monkeypatch.setenv("API_ENABLED", "true")
    monkeypatch.setenv("API_AUTH_TOKEN", "testtoken")

    action = GatewayActionFactory()

    response = client.patch(
        f"/dicom/{action.id}/failure",
        json={"error": "Missing PatientID"},
        headers={"Authorization": "Bearer testtoken"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "failure recorded"

    action.refresh_from_db()
    assert action.status == GatewayActionStatus.IMAGE_FAILED
    assert action.last_error == "Missing PatientID"
    assert action.failed_at is not None


@pytest.mark.django_db
def test_report_failure_action_not_found(monkeypatch):
    monkeypatch.setenv("API_ENABLED", "true")
    monkeypatch.setenv("API_AUTH_TOKEN", "testtoken")

    response = client.patch(
        "/dicom/00000000-0000-0000-0000-000000000000/failure",
        json={"error": "Missing PatientID"},
        headers={"Authorization": "Bearer testtoken"},
    )

    assert response.status_code == 404
    assert response.json()["title"] == "Not Found"
