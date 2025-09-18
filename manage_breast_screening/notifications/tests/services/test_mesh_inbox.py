from unittest.mock import ANY, MagicMock, patch

import pytest

from manage_breast_screening.notifications.services.mesh_inbox import MeshInbox


@patch("manage_breast_screening.notifications.services.mesh_inbox.MeshClient")
class TestMeshInbox:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        monkeypatch.setenv("NBSS_MESH_HOST", "https://mesh.test")
        monkeypatch.setenv("NBSS_MESH_INBOX_NAME", "mesh-inbox-name")
        monkeypatch.setenv("NBSS_MESH_PASSWORD", "mesh-password")
        monkeypatch.setenv("NBSS_MESH_SHARED_KEY", "mesh-shared-key")
        monkeypatch.setenv("NBSS_MESH_CERT", "mesh-cert")
        monkeypatch.setenv("NBSS_MESH_PRIVATE_KEY", "mesh-private-key")
        monkeypatch.setenv("NBSS_MESH_CA_CERT", "mesh-ca-cert")

    def test_client_initialises(self, mock_mesh_client):
        with patch.object(
            MeshInbox,
            "ssl_credentials",
            return_value=("cert", "private-key", "ca-cert"),
        ):
            MeshInbox()

        mock_mesh_client.assert_called_once_with(
            url="https://mesh.test",
            mailbox="mesh-inbox-name",
            password="mesh-password",
            shared_key="mesh-shared-key",
            cert=("cert", "private-key"),
            verify="ca-cert",
        )

    def test_constructor_as_contextmanager(self, mock_mesh_client):
        with MeshInbox() as inbox:
            inbox.fetch_message_ids()

        mock_mesh_client.assert_called_once_with(
            url="https://mesh.test",
            mailbox="mesh-inbox-name",
            password="mesh-password",
            shared_key="mesh-shared-key",
            cert=(ANY, ANY),
            verify=ANY,
        )
        mock_mesh_client.return_value.list_messages.assert_called_once()
        mock_mesh_client.return_value.close.assert_called_once()

    def test_ssl_credentials(self, _unused_mock):
        mock_cert_file = MagicMock()
        mock_cert_file.name = "cert"
        mock_private_key_file = MagicMock()
        mock_private_key_file.name = "private-key"
        mock_ca_cert_file = MagicMock()
        mock_ca_cert_file.name = "ca-cert"

        with patch.object(
            MeshInbox,
            "to_file",
            side_effect=[mock_cert_file, mock_private_key_file, mock_ca_cert_file],
        ):
            cert_file_name, private_key_file_name, ca_cert_file_name = (
                MeshInbox.ssl_credentials()
            )

        assert cert_file_name == "cert"
        assert private_key_file_name == "private-key"
        assert ca_cert_file_name == "ca-cert"

    def test_fetch_message_ids(self, mock_mesh_client):
        MeshInbox().fetch_message_ids()

        mock_mesh_client.return_value.list_messages.assert_called_once()

    def test_fetch_message(self, mock_mesh_client):
        MeshInbox().fetch_message("some-message-id")

        mock_mesh_client.return_value.retrieve_message.assert_called_once_with(
            "some-message-id"
        )

    def test_acknowledge(self, mock_mesh_client):
        MeshInbox().acknowledge("a-message-id")

        mock_mesh_client.return_value.acknowledge_message.assert_called_once_with(
            "a-message-id"
        )
