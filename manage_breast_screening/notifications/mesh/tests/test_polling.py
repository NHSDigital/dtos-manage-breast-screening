"""
Tests for MESH polling functionality
"""

from datetime import datetime
from io import StringIO
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.test import TestCase

from manage_breast_screening.notifications.appointments.appointment_details import (
    store_new_message,
)
from manage_breast_screening.notifications.mesh.polling import (
    get_mesh_inbox_messages,
    get_mesh_message_content,
    run_mesh_polling,
)
from manage_breast_screening.notifications.storage.azure import (
    get_azure_blob_client,
    store_message_to_blob,
)


class TestMeshPollingFunctions(TestCase):
    """Test the core MESH polling functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_blob_service_client = Mock()
        self.mock_blob_client = Mock()
        self.mock_blob_service_client.get_blob_client.return_value = (
            self.mock_blob_client
        )

    @patch("manage_breast_screening.notifications.storage.azure.settings")
    def test_get_azure_blob_client_success(self, mock_settings):
        """Test successful Azure Blob client creation"""
        mock_settings.AZURE_STORAGE_CONNECTION_STRING = "test_connection_string"

        with patch(
            "manage_breast_screening.notifications.storage.azure.BlobServiceClient"
        ) as mock_blob_service:
            mock_blob_service.from_connection_string.return_value = (
                self.mock_blob_service_client
            )

            result = get_azure_blob_client()

            mock_blob_service.from_connection_string.assert_called_once_with(
                "test_connection_string"
            )
            self.assertEqual(result, self.mock_blob_service_client)

    @patch("manage_breast_screening.notifications.storage.azure.settings")
    def test_get_azure_blob_client_no_connection_string(self, mock_settings):
        """Test Azure Blob client creation fails when no connection string"""
        mock_settings.AZURE_STORAGE_CONNECTION_STRING = None

        with patch(
            "manage_breast_screening.notifications.storage.azure.os.getenv"
        ) as mock_getenv:
            mock_getenv.return_value = None

            with self.assertRaises(ValueError) as context:
                get_azure_blob_client()

            self.assertIn(
                "Azure Storage connection string not configured", str(context.exception)
            )

    @patch("manage_breast_screening.notifications.mesh.polling.requests.get")
    def test_get_mesh_inbox_messages_success(self, mock_get):
        """Test successful retrieval of MESH inbox messages"""
        mock_response = Mock()
        mock_response.json.return_value = [
            {"id": "BSO_20240115T143022"},
            {"id": "ABC_20240115T143045"},
            {"id": "XYZ_20240115T143108"},
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_mesh_inbox_messages()

        expected_ids = [
            "BSO_20240115T143022",
            "ABC_20240115T143045",
            "XYZ_20240115T143108",
        ]
        self.assertEqual(result, expected_ids)
        mock_get.assert_called_once_with(
            "https://localhost:8700/messageexchange/X26ABC1/inbox",
            verify=False,
            timeout=30,
        )

    @patch("manage_breast_screening.notifications.mesh.polling.requests.get")
    def test_get_mesh_inbox_messages_empty_response(self, mock_get):
        """Test handling of empty MESH inbox response"""
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_mesh_inbox_messages()

        self.assertEqual(result, [])

    @patch("manage_breast_screening.notifications.mesh.polling.requests.get")
    def test_get_mesh_inbox_messages_request_failure(self, mock_get):
        """Test handling of MESH API request failure"""
        mock_get.side_effect = Exception("Connection failed")

        with self.assertRaises(Exception):
            get_mesh_inbox_messages()

    @patch("manage_breast_screening.notifications.mesh.polling.requests.get")
    def test_get_mesh_message_content_success(self, mock_get):
        """Test successful retrieval of MESH message content"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "BSO_20240115T143022",
            "filename": "BSO_test_message.dat",
            "content": b"test message content",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_mesh_message_content("BSO_20240115T143022")

        expected_message = {
            "id": "BSO_20240115T143022",
            "content": b"test message content",
            "filename": "BSO_test_message.dat",
            "bso_code": "BSO",
            "metadata": {
                "id": "BSO_20240115T143022",
                "filename": "BSO_test_message.dat",
                "content": b"test message content",
            },
        }
        self.assertEqual(result, expected_message)
        mock_get.assert_called_once_with(
            "https://localhost:8700/messageexchange/X26ABC1/inbox/BSO_20240115T143022",
            verify=False,
            timeout=30,
        )

    @patch("manage_breast_screening.notifications.mesh.polling.requests.get")
    def test_get_mesh_message_content_no_filename(self, mock_get):
        """Test handling of message with no filename"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "BSO_20240115T143022",
            "content": b"test message content",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_mesh_message_content("BSO_20240115T143022")

        self.assertEqual(result["bso_code"], "UNK")

    def test_store_message_to_blob_success(self):
        """Test successful storage of message to Azure Blob"""
        message = {
            "id": "BSO_20240115T143022",
            "content": b"test message content",
            "bso_code": "BSO",
        }
        fixed_dt = datetime(2024, 1, 15, 14, 30, 22)
        with patch(
            "manage_breast_screening.notifications.storage.azure.datetime"
        ) as mock_datetime:
            mock_datetime.now.return_value = fixed_dt
            store_message_to_blob(self.mock_blob_service_client, message)
            self.mock_blob_service_client.get_blob_client.assert_called_once_with(
                container="mesh-messages", blob="2024-01-15/BSO_20240115T143022.dat"
            )
            self.mock_blob_client.upload_blob.assert_called_once_with(
                b"test message content", overwrite=True
            )

    def test_store_message_to_blob_string_content(self):
        """Test storage of message with string content (should be encoded)"""
        message = {
            "id": "BSO_20240115T143022",
            "content": "test message content",
            "bso_code": "BSO",
        }
        fixed_dt = datetime(2024, 1, 15, 14, 30, 22)
        with patch(
            "manage_breast_screening.notifications.storage.azure.datetime"
        ) as mock_datetime:
            mock_datetime.now.return_value = fixed_dt
            store_message_to_blob(self.mock_blob_service_client, message)
            self.mock_blob_client.upload_blob.assert_called_once_with(
                b"test message content", overwrite=True
            )

    @patch("manage_breast_screening.notifications.mesh.polling.get_azure_blob_client")
    @patch("manage_breast_screening.notifications.mesh.polling.get_mesh_inbox_messages")
    @patch(
        "manage_breast_screening.notifications.mesh.polling.get_mesh_message_content"
    )
    @patch("manage_breast_screening.notifications.mesh.polling.store_message_to_blob")
    def test_run_mesh_polling_success(
        self, mock_store, mock_get_content, mock_get_inbox, mock_get_blob
    ):
        """Test successful end-to-end MESH polling process"""
        # Setup mocks
        mock_get_blob.return_value = self.mock_blob_service_client
        mock_get_inbox.return_value = ["BSO_20240115T143022", "ABC_20240115T143045"]

        mock_message1 = {
            "id": "BSO_20240115T143022",
            "content": b"content1",
            "bso_code": "BSO",
        }
        mock_message2 = {
            "id": "ABC_20240115T143045",
            "content": b"content2",
            "bso_code": "ABC",
        }
        mock_get_content.side_effect = [mock_message1, mock_message2]

        # Run the polling process
        run_mesh_polling()

        # Verify all functions were called correctly
        mock_get_blob.assert_called_once()
        mock_get_inbox.assert_called_once()
        self.assertEqual(mock_get_content.call_count, 2)
        self.assertEqual(mock_store.call_count, 2)

    @patch("manage_breast_screening.notifications.mesh.polling.get_azure_blob_client")
    @patch("manage_breast_screening.notifications.mesh.polling.get_mesh_inbox_messages")
    def test_run_mesh_polling_empty_inbox(self, mock_get_inbox, mock_get_blob):
        """Test MESH polling with empty inbox"""
        mock_get_blob.return_value = self.mock_blob_service_client
        mock_get_inbox.return_value = []

        # Run the polling process
        run_mesh_polling()

        # Verify functions were called but no messages processed
        mock_get_blob.assert_called_once()
        mock_get_inbox.assert_called_once()

    @patch("manage_breast_screening.notifications.mesh.polling.get_azure_blob_client")
    @patch("manage_breast_screening.notifications.mesh.polling.get_mesh_inbox_messages")
    @patch(
        "manage_breast_screening.notifications.mesh.polling.get_mesh_message_content"
    )
    @patch("manage_breast_screening.notifications.mesh.polling.store_message_to_blob")
    def test_run_mesh_polling_partial_failure(
        self, mock_store, mock_get_content, mock_get_inbox, mock_get_blob
    ):
        """Test MESH polling with some message processing failures"""
        # Setup mocks
        mock_get_blob.return_value = self.mock_blob_service_client
        mock_get_inbox.return_value = ["BSO_20240115T143022", "ABC_20240115T143045"]

        # First message succeeds, second fails
        mock_message1 = {
            "id": "BSO_20240115T143022",
            "content": b"content1",
            "bso_code": "BSO",
        }
        mock_get_content.side_effect = [mock_message1, Exception("API Error")]

        # Run the polling process
        run_mesh_polling()

        # Verify first message was processed, second was skipped
        self.assertEqual(mock_get_content.call_count, 2)
        self.assertEqual(mock_store.call_count, 1)


class TestStoreNewMessage(TestCase):
    """Test the refactored store_new_message function"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_blob_client = Mock()
        self.mock_blob_client.get_blob_client.return_value = Mock()

    def test_store_new_message_success(self):
        """Test successful storage with new filename structure"""
        message = {"id": "BSO_20240115T143022", "content": b"test message content"}
        fixed_dt = datetime(2024, 1, 15, 14, 30, 22)
        with patch(
            "manage_breast_screening.notifications.appointments.appointment_details.datetime"
        ) as mock_datetime:
            mock_datetime.now.return_value = fixed_dt
            store_new_message(self.mock_blob_client, message)
            self.mock_blob_client.get_blob_client.assert_called_once_with(
                "2024-01-15/BSO_20240115T143022.dat"
            )

    def test_store_new_message_short_id(self):
        """Test storage with short message ID (less than 3 characters)"""
        message = {"id": "AB", "content": b"test message content"}
        fixed_dt = datetime(2024, 1, 15, 14, 30, 22)
        with patch(
            "manage_breast_screening.notifications.appointments.appointment_details.datetime"
        ) as mock_datetime:
            mock_datetime.now.return_value = fixed_dt
            store_new_message(self.mock_blob_client, message)
            self.mock_blob_client.get_blob_client.assert_called_once_with(
                "2024-01-15/AB_20240115T143022.dat"
            )

    def test_store_new_message_no_id(self):
        """Test storage with no message ID"""
        message = {"id": "", "content": b"test message content"}
        fixed_dt = datetime(2024, 1, 15, 14, 30, 22)
        with patch(
            "manage_breast_screening.notifications.appointments.appointment_details.datetime"
        ) as mock_datetime:
            mock_datetime.now.return_value = fixed_dt
            store_new_message(self.mock_blob_client, message)
            self.mock_blob_client.get_blob_client.assert_called_once_with(
                "2024-01-15/UNK_20240115T143022.dat"
            )


class TestMeshPollingManagementCommand(TestCase):
    """Test the Django management command"""

    def test_poll_mesh_inbox_command_success(self):
        """Test successful execution of the management command"""
        with patch(
            "manage_breast_screening.notifications.management.commands.poll_mesh_inbox.run_mesh_polling"
        ) as mock_run:
            out = StringIO()

            call_command("poll_mesh_inbox", stdout=out)

            mock_run.assert_called_once()
            self.assertIn("Starting MESH inbox polling process", out.getvalue())

    def test_poll_mesh_inbox_command_failure(self):
        """Test management command handles failures gracefully"""
        with patch(
            "manage_breast_screening.notifications.management.commands.poll_mesh_inbox.run_mesh_polling"
        ) as mock_run:
            mock_run.side_effect = Exception("Test error")
            out = StringIO()

            with self.assertRaises(Exception):
                call_command("poll_mesh_inbox", stdout=out)

            self.assertIn("MESH inbox polling failed", out.getvalue())

    def test_poll_mesh_inbox_command_dry_run(self):
        """Test management command with dry-run flag"""
        with patch(
            "manage_breast_screening.notifications.management.commands.poll_mesh_inbox.run_mesh_polling"
        ) as mock_run:
            out = StringIO()

            call_command("poll_mesh_inbox", "--dry-run", stdout=out)

            # Note: Currently dry-run doesn't change behaviour, but flag is accepted
            mock_run.assert_called_once()
