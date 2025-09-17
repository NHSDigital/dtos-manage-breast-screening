import uuid
from datetime import datetime
from unittest.mock import patch

import pytest

from manage_breast_screening.notifications.management.commands.create_appointments import (
    Command as CreateAppointmentsCommand,
)
from manage_breast_screening.notifications.management.commands.send_message_batch import (
    Command as SendMessageBatchCommand,
)
from manage_breast_screening.notifications.management.commands.store_mesh_messages import (
    Command as StoreMeshMessagesCommand,
)
from manage_breast_screening.notifications.tests.integration.helpers import Helpers


@patch("manage_breast_screening.notifications.services.api_client.jwt.encode")
class TestEndToEnd:
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

        monkeypatch.setenv(
            "NHS_NOTIFY_API_MESSAGE_BATCH_URL", "http://localhost:8888/message/batch"
        )
        monkeypatch.setenv("API_OAUTH_TOKEN_URL", "http://localhost:8888/token")
        monkeypatch.setenv("API_OAUTH_API_KEY", "a1b2c3d4")
        monkeypatch.setenv("API_OAUTH_API_KID", "test-1")

        monkeypatch.setenv("PRIVATE_KEY", "test-key")

    @pytest.mark.django_db
    def test_get_from_mesh_and_send_message_batch(self, mock_jwt_encode):
        helpers = Helpers()
        test_file_1 = helpers.get_test_file_path("ABC_20241202091221_APPT_106.dat")
        test_file_2 = helpers.get_test_file_path("ABC_20241202091321_APPT_107.dat")
        helpers.add_file_to_mesh_mailbox(test_file_1)
        helpers.add_file_to_mesh_mailbox(test_file_2)

        store_mesh_messages = StoreMeshMessagesCommand()
        store_mesh_messages.handle()

        today_dirname = datetime.today().strftime("%Y-%m-%d")
        CreateAppointmentsCommand().handle(**{"date_str": today_dirname})

        routing_plan = str(uuid.uuid4())
        send_message_batch = SendMessageBatchCommand()
        send_message_batch.handle(**{"routing_plan_id": routing_plan})

        # do we want to perform the failed message batch command here? or save that for another test?
