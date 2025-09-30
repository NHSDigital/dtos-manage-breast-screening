from datetime import datetime
from unittest.mock import patch

import pytest

from manage_breast_screening.notifications.management.commands.create_appointments import (
    Command as CreateAppointments,
)
from manage_breast_screening.notifications.management.commands.send_message_batch import (
    Command as SendMessageBatch,
)
from manage_breast_screening.notifications.management.commands.store_mesh_messages import (
    Command as StoreMeshMessages,
)
from manage_breast_screening.notifications.models import (
    Appointment,
    MessageBatch,
    MessageBatchStatusChoices,
)
from manage_breast_screening.notifications.tests.integration.helpers import Helpers


@patch("manage_breast_screening.notifications.services.api_client.jwt.encode")
class TestEndToEnd:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
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
        monkeypatch.setenv("BLOB_CONTAINER_NAME", "nbss-appoinments-data")

        monkeypatch.setenv(
            "NHS_NOTIFY_API_MESSAGE_BATCH_URL", "http://localhost:8888/message/batch"
        )
        monkeypatch.setenv("API_OAUTH_TOKEN_URL", "http://localhost:8888/token")
        monkeypatch.setenv("API_OAUTH_API_KEY", "a1b2c3d4")
        monkeypatch.setenv("API_OAUTH_API_KID", "test-1")

        monkeypatch.setenv("API_OAUTH_PRIVATE_KEY", "test-key")

    @pytest.mark.django_db
    def test_get_from_mesh_and_send_message_batch(self, mock_jwt_encode):
        helpers = Helpers()
        test_file_1 = helpers.get_test_file_path("ABC_20241202091221_APPT_106.dat")
        test_file_2 = helpers.get_test_file_path("ABC_20241202091321_APPT_107.dat")
        helpers.add_file_to_mesh_mailbox(test_file_1)
        helpers.add_file_to_mesh_mailbox(test_file_2)

        StoreMeshMessages().handle()

        today_dirname = datetime.today().strftime("%Y-%m-%d")
        CreateAppointments().handle(**{"date_str": today_dirname})

        assert Appointment.objects.filter(episode_type="F").count() == 1
        assert Appointment.objects.filter(episode_type="S").count() == 1

        send_message_batch = SendMessageBatch()
        send_message_batch.handle()

        assert (
            MessageBatch.objects.filter(
                status=MessageBatchStatusChoices.SENT.value
            ).count()
            == 1
        )
