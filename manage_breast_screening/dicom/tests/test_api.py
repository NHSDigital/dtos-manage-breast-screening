import io
import os

import pydicom
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from ninja.testing import TestClient

from manage_breast_screening.core.api import api
from manage_breast_screening.dicom.models import Study

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

    response = client.put(
        "/dicom/abc123",
        FILES={"file": dicom_file},
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

    response = client.put(
        "/dicom/abc123",
        FILES={"file": None},
    )

    assert response.status_code == 422


def test_upload_invalid_file(monkeypatch):
    monkeypatch.setenv("API_ENABLED", "true")

    invalid_file = SimpleUploadedFile(
        "invalid.dcm", b"not a dicom file", content_type="application/dicom"
    )

    response = client.put(
        "/dicom/abc123",
        FILES={"file": invalid_file},
    )

    assert response.status_code == 400
    assert response.json()["title"] == "Invalid DICOM file"
    assert response.json()["status"] == 400
    assert response.json()["detail"] == "The uploaded file is not a valid DICOM file."


def test_upload_missing_uids(dataset, monkeypatch):
    monkeypatch.setenv("API_ENABLED", "true")

    del dataset.StudyInstanceUID
    del dataset.SeriesInstanceUID
    del dataset.SOPInstanceUID

    with io.BytesIO() as buffer:
        pydicom.dcmwrite(buffer, dataset, enforce_file_format=True)
        buffer.seek(0)
        dicom_file = SimpleUploadedFile(
            "temp.dcm", buffer.read(), content_type="application/dicom"
        )

    response = client.put(
        "/dicom/abc123",
        FILES={"file": dicom_file},
    )

    assert response.status_code == 400
    assert response.json()["title"] == "Missing DICOM attributes"
    assert response.json()["status"] == 400
    assert (
        response.json()["detail"]
        == "The DICOM file is missing required UID attributes."
    )


@pytest.mark.django_db
def test_upload_when_api_disabled(dicom_file, monkeypatch):
    monkeypatch.setenv("API_ENABLED", "false")

    response = client.put(
        "/dicom/abc123",
        FILES={"file": dicom_file},
    )

    assert response.status_code == 403
    assert response.json()["status"] == "API is not available"
