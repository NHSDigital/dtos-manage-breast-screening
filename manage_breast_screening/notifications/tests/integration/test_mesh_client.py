import os

import pytest
from mesh_client import MeshClient

from manage_breast_screening.notifications.tests.integration.helpers import Helpers


@pytest.mark.integration
class TestMeshClient:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        monkeypatch.setenv("NBSS_MESH_HOST", "http://localhost:8700")
        monkeypatch.setenv("NBSS_MESH_PASSWORD", "password")
        monkeypatch.setenv("NBSS_MESH_SHARED_KEY", "TestKey")
        monkeypatch.setenv("NBSS_MESH_INBOX_NAME", "X26ABC1")

    @pytest.fixture
    def helpers(self):
        return Helpers()

    def test_retrieve_file(self, helpers):
        test_file_path = helpers.get_test_file_path("ABC_20241202091221_APPT_106.dat")
        helpers.add_file_to_mesh_mailbox(test_file_path)

        with MeshClient(
            url=os.getenv("NBSS_MESH_HOST"),
            mailbox=os.getenv("NBSS_MESH_INBOX_NAME"),
            password=os.getenv("NBSS_MESH_PASSWORD"),
            shared_key=os.getenv("NBSS_MESH_SHARED_KEY"),
        ) as client:
            message_ids = client.list_messages()

            assert len(message_ids) == 1

            message_id = message_ids[0]
            message = client.retrieve_message(message_id).read().decode("ASCII")

            with open(test_file_path) as test_file:
                assert message == test_file.read()

            client.acknowledge_message(message_ids[0])
