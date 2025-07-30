import pytest

from manage_breast_screening.notifications.management.commands.get_appointment_details import (
    Command,
)
from manage_breast_screening.notifications.tests.integration.helpers import Helpers


@pytest.mark.integration
class TestMeshClient:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        monkeypatch.setenv("MESH_BASE_URL", "http://localhost:8700")
        monkeypatch.setenv("MESH_CLIENT_PASSWORD", "password")
        monkeypatch.setenv("MESH_CLIENT_SHARED_KEY", "TestKey")
        monkeypatch.setenv("MESH_INBOX_NAME", "X26ABC1")

        monkeypatch.setenv(
            "BLOB_STORAGE_CONNECTION_STRING", Helpers().azurite_connection_string()
        )
        monkeypatch.setenv("BLOB_CONTAINER_NAME", "nbss-appoinments-data")

    @pytest.fixture
    def helpers(self):
        return Helpers()

    def test_retrieve_file(self, helpers):
        test_file_path = helpers.test_dat_file_path()
        helpers.add_file_to_mesh_mailbox(test_file_path)

        subject = Command()

        subject.handle()

        # subject.handle()

        # message = subject.get_appointment_details(client, message_id).read().decode("ASCII")

        # with open(test_file_path) as test_file:
        #     assert message == test_file.read()

        # client.acknowledge_message(message_ids[0])
