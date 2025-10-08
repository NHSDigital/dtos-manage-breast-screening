import pytest

from manage_breast_screening.notifications.tests.integration.helpers import Helpers


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    monkeypatch.setenv("DJANGO_ENV", "test")
    monkeypatch.setenv("NBSS_MESH_HOST", "http://localhost:8700")
    monkeypatch.setenv("NBSS_MESH_PASSWORD", "password")
    monkeypatch.setenv("NBSS_MESH_SHARED_KEY", "TestKey")
    monkeypatch.setenv("NBSS_MESH_INBOX_NAME", "X26ABC1")
    monkeypatch.setenv("NBSS_MESH_CERT", "mesh-cert")
    monkeypatch.setenv("NBSS_MESH_PRIVATE_KEY", "mesh-private-key")
    monkeypatch.setenv("NBSS_MESH_CA_CERT", "mesh-ca-cert")

    monkeypatch.setenv(
        "BLOB_STORAGE_CONNECTION_STRING", Helpers().azurite_connection_string()
    )
    monkeypatch.setenv(
        "QUEUE_STORAGE_CONNECTION_STRING", Helpers().azurite_connection_string()
    )
    monkeypatch.setenv("BLOB_CONTAINER_NAME", "nbss-appoinments-data")
    monkeypatch.setenv(
        "NHS_NOTIFY_API_MESSAGE_BATCH_URL", "http://localhost:8888/message/batch"
    )
    monkeypatch.setenv("API_OAUTH_TOKEN_URL", "http://localhost:8888/token")
    monkeypatch.setenv("API_OAUTH_API_KEY", "a1b2c3d4")
    monkeypatch.setenv("API_OAUTH_API_KID", "test-1")

    monkeypatch.setenv("API_OAUTH_PRIVATE_KEY", "test-key")
