import io
import tempfile

import pydicom
import pytest
from django.test import Client


@pytest.fixture(autouse=True)
def enable_dicom_api_settings(monkeypatch):
    monkeypatch.setenv("DICOM_API_ENABLED", "true")


@pytest.mark.django_db
def test_upload_dicom(dataset):
    client = Client(HTTP_X_SOURCE_MESSAGE_ID="test-source-message-id")
    buffer = io.BytesIO()
    memory_file = pydicom.filebase.DicomFileLike(buffer)
    pydicom.dcmwrite(memory_file, dataset)
    memory_file.seek(0)
    response = client.post(
        "/api/dicom/upload/",
        content_type="application/dicom",
        data=memory_file,
    )
    assert response.status_code == 201
    assert response.json()["study_instance_uid"] == dataset.StudyInstanceUID
    assert response.json()["series_instance_uid"] == dataset.SeriesInstanceUID
    assert response.json()["sop_instance_uid"] == dataset.SOPInstanceUID
    assert "instance_id" in response.json()


def test_upload_dicom_missing_header(dataset):
    client = Client()
    with tempfile.NamedTemporaryFile() as temp_file:
        pydicom.filewriter.dcmwrite(temp_file.name, dataset, write_like_original=False)
        with open(temp_file.name, "rb") as dicom_file:
            response = client.post(
                "/api/dicom/upload/",
                {"file": dicom_file},
            )
    assert response.status_code == 400
    assert response.json()["error"] == "Missing X-Source-Message-ID header"


def test_upload_dicom_no_file():
    client = Client(HTTP_X_SOURCE_MESSAGE_ID="test-source-message-id")
    response = client.post("/api/dicom/upload/", {})
    assert response.status_code == 400
    assert response.json()["error"] == "No DICOM file provided"


def test_upload_dicom_invalid_method():
    client = Client(HTTP_X_SOURCE_MESSAGE_ID="test-source-message-id")
    response = client.get("/api/dicom/upload/")
    assert response.status_code == 405


def test_upload_dicom_invalid_file():
    client = Client(HTTP_X_SOURCE_MESSAGE_ID="test-source-message-id")
    response = client.post(
        "/api/dicom/upload/",
        {"file": tempfile.TemporaryFile()},
    )
    assert response.status_code == 400
    assert response.json()["error"] == "Invalid DICOM file"


def test_upload_dicom_missing_uids(dataset):
    client = Client(HTTP_X_SOURCE_MESSAGE_ID="test-source-message-id")
    del dataset.StudyInstanceUID
    del dataset.SeriesInstanceUID
    del dataset.SOPInstanceUID
    with tempfile.NamedTemporaryFile() as temp_file:
        pydicom.filewriter.dcmwrite(temp_file.name, dataset, write_like_original=False)
        with open(temp_file.name, "rb") as dicom_file:
            response = client.post(
                "/api/dicom/upload/",
                {"file": dicom_file},
            )
    assert response.status_code == 400
    assert response.json()["error"] == "Missing required DICOM UIDs"


@pytest.mark.django_db
def test_upload_dicom_duplicate(dataset):
    client = Client(HTTP_X_SOURCE_MESSAGE_ID="test-source-message-id")

    with tempfile.NamedTemporaryFile() as temp_file:
        pydicom.filewriter.dcmwrite(temp_file.name, dataset, write_like_original=False)
        with open(temp_file.name, "rb") as dicom_file:
            response1 = client.post(
                "/api/dicom/upload/",
                {"file": dicom_file},
            )
        assert response1.status_code == 201

        with open(temp_file.name, "rb") as dicom_file:
            response2 = client.post(
                "/api/dicom/upload/",
                {"file": dicom_file},
            )
    assert response2.status_code == 409
    assert response2.json()["error"] == "DICOM instance already exists"


def test_upload_dicom_unexpected_error(monkeypatch, dataset):
    client = Client(HTTP_X_SOURCE_MESSAGE_ID="test-source-message-id")

    def raise_exception(*args, **kwargs):
        raise Exception("Unexpected error")

    monkeypatch.setattr("pydicom.dcmread", raise_exception)

    with tempfile.NamedTemporaryFile() as temp_file:
        pydicom.filewriter.dcmwrite(temp_file.name, dataset, write_like_original=False)
        with open(temp_file.name, "rb") as dicom_file:
            response = client.post(
                "/api/dicom/upload/",
                {"file": dicom_file},
            )
    assert response.status_code == 500
    assert "An error occurred: Unexpected error" in response.json()["error"]


@pytest.mark.django_db
def test_upload_dicom_api_disabled(monkeypatch, dataset):
    monkeypatch.setenv("DICOM_API_ENABLED", "false")
    client = Client(HTTP_X_SOURCE_MESSAGE_ID="test-source-message-id")
    with tempfile.NamedTemporaryFile() as temp_file:
        pydicom.filewriter.dcmwrite(temp_file.name, dataset, write_like_original=False)
        with open(temp_file.name, "rb") as dicom_file:
            response = client.post(
                "/api/dicom/upload/",
                {"file": dicom_file},
            )
    assert response.status_code == 403
