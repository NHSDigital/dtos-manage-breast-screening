import os

import pytest
from mesh_client import MeshClient

from manage_breast_screening.notifications.tests.integration.helpers import Helpers


@pytest.mark.integration
class TestMeshClient:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        monkeypatch.setenv("MESH_BASE_URL", "http://localhost:8700")
        monkeypatch.setenv("MESH_CLIENT_PASSWORD", "password")
        monkeypatch.setenv("MESH_CLIENT_SHARED_KEY", "TestKey")
        monkeypatch.setenv("MESH_INBOX_NAME", "X26ABC1")

    def test_retrieve_file(self):
        test_file_path = f"{os.path.dirname(os.path.realpath(__file__))}/../management/commands/test.dat"
        Helpers().add_file_to_mesh_mailbox(test_file_path)

        with MeshClient(
            url=os.getenv("MESH_BASE_URL"),
            mailbox=os.getenv("MESH_INBOX_NAME"),
            password=os.getenv("MESH_CLIENT_PASSWORD"),
            shared_key=os.getenv("MESH_CLIENT_SHARED_KEY"),
        ) as client:
            message_ids = client.list_messages()

            assert len(message_ids) == 1

            message = client.retrieve_message(message_ids[0]).read().decode("ASCII")

            with open(test_file_path) as test_file:
                assert message == test_file.read()

            client.acknowledge_message(message_ids[0])
