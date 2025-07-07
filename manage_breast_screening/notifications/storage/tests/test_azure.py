"""
Tests for Azure Storage functionality
"""

from datetime import datetime
from unittest.mock import Mock, patch

from django.test import TestCase

from manage_breast_screening.notifications.storage.azure import (
    delete_blob,
    get_azure_blob_client,
    list_blobs_in_container,
    store_message_to_blob,
)


class TestAzureStorageFunctions(TestCase):
    """Test the Azure Storage utility functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_blob_service_client = Mock()
        self.mock_blob_client = Mock()
        self.mock_container_client = Mock()
        self.mock_blob_service_client.get_blob_client.return_value = (
            self.mock_blob_client
        )
        self.mock_blob_service_client.get_container_client.return_value = (
            self.mock_container_client
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

    @patch("manage_breast_screening.notifications.storage.azure.settings")
    def test_get_azure_blob_client_environment_fallback(self, mock_settings):
        """Test Azure Blob client creation uses environment variable as fallback"""
        mock_settings.AZURE_STORAGE_CONNECTION_STRING = None

        with patch(
            "manage_breast_screening.notifications.storage.azure.os.getenv"
        ) as mock_getenv:
            mock_getenv.return_value = "env_connection_string"

            with patch(
                "manage_breast_screening.notifications.storage.azure.BlobServiceClient"
            ) as mock_blob_service:
                mock_blob_service.from_connection_string.return_value = (
                    self.mock_blob_service_client
                )

                result = get_azure_blob_client()

                mock_getenv.assert_called_once_with("AZURE_STORAGE_CONNECTION_STRING")
                mock_blob_service.from_connection_string.assert_called_once_with(
                    "env_connection_string"
                )
                self.assertEqual(result, self.mock_blob_service_client)

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

            expected_blob_path = "2024-01-15/BSO_20240115T143022.dat"
            self.mock_blob_service_client.get_blob_client.assert_called_once_with(
                container="mesh-messages", blob=expected_blob_path
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

    def test_store_message_to_blob_no_id(self):
        """Test storage fails when message has no ID"""
        message = {"content": b"test message content", "bso_code": "BSO"}

        with self.assertRaises(ValueError) as context:
            store_message_to_blob(self.mock_blob_service_client, message)

        self.assertIn("Message ID is required", str(context.exception))

    def test_store_message_to_blob_no_content(self):
        """Test storage fails when message has no content"""
        message = {"id": "BSO_20240115T143022", "bso_code": "BSO"}

        with self.assertRaises(ValueError) as context:
            store_message_to_blob(self.mock_blob_service_client, message)

        self.assertIn("Message content is required", str(context.exception))

    def test_store_message_to_blob_unknown_bso_code(self):
        """Test storage with unknown BSO code (should use UNK)"""
        message = {
            "id": "BSO_20240115T143022",
            "content": b"test message content",
            # No bso_code provided
        }

        fixed_dt = datetime(2024, 1, 15, 14, 30, 22)
        with patch(
            "manage_breast_screening.notifications.storage.azure.datetime"
        ) as mock_datetime:
            mock_datetime.now.return_value = fixed_dt

            store_message_to_blob(self.mock_blob_service_client, message)

            expected_blob_path = "2024-01-15/UNK_20240115T143022.dat"
            self.mock_blob_service_client.get_blob_client.assert_called_with(
                container="mesh-messages", blob=expected_blob_path
            )

    @patch("manage_breast_screening.notifications.storage.azure.get_azure_blob_client")
    def test_list_blobs_in_container_success(self, mock_get_client):
        """Test successful listing of blobs in container"""
        mock_get_client.return_value = self.mock_blob_service_client

        # Mock blob list
        mock_blob1 = Mock()
        mock_blob1.name = "2024-01-15/BSO_20240115T143022.dat"
        mock_blob2 = Mock()
        mock_blob2.name = "2024-01-15/ABC_20240115T143045.dat"

        self.mock_container_client.list_blobs.return_value = [mock_blob1, mock_blob2]

        result = list_blobs_in_container()

        expected_blobs = [
            "2024-01-15/BSO_20240115T143022.dat",
            "2024-01-15/ABC_20240115T143045.dat",
        ]
        self.assertEqual(result, expected_blobs)

        self.mock_blob_service_client.get_container_client.assert_called_once_with(
            "mesh-messages"
        )
        self.mock_container_client.list_blobs.assert_called_once_with(
            name_starts_with=None
        )

    @patch("manage_breast_screening.notifications.storage.azure.get_azure_blob_client")
    def test_list_blobs_in_container_with_prefix(self, mock_get_client):
        """Test listing blobs with prefix filter"""
        mock_get_client.return_value = self.mock_blob_service_client

        # Mock blob list
        mock_blob = Mock()
        mock_blob.name = "2024-01-15/BSO_20240115T143022.dat"

        self.mock_container_client.list_blobs.return_value = [mock_blob]

        result = list_blobs_in_container(prefix="2024-01-15/BSO")

        expected_blobs = ["2024-01-15/BSO_20240115T143022.dat"]
        self.assertEqual(result, expected_blobs)

        self.mock_container_client.list_blobs.assert_called_once_with(
            name_starts_with="2024-01-15/BSO"
        )

    @patch("manage_breast_screening.notifications.storage.azure.get_azure_blob_client")
    def test_delete_blob_success(self, mock_get_client):
        """Test successful deletion of blob"""
        mock_get_client.return_value = self.mock_blob_service_client

        result = delete_blob("2024-01-15/BSO_20240115T143022.dat")

        self.assertTrue(result)
        self.mock_blob_service_client.get_blob_client.assert_called_once_with(
            container="mesh-messages", blob="2024-01-15/BSO_20240115T143022.dat"
        )
        self.mock_blob_client.delete_blob.assert_called_once()

    @patch("manage_breast_screening.notifications.storage.azure.get_azure_blob_client")
    def test_delete_blob_custom_container(self, mock_get_client):
        """Test deletion of blob from custom container"""
        mock_get_client.return_value = self.mock_blob_service_client

        result = delete_blob("2024-01-15/BSO_20240115T143022.dat", "custom-container")

        self.assertTrue(result)
        self.mock_blob_service_client.get_blob_client.assert_called_once_with(
            container="custom-container", blob="2024-01-15/BSO_20240115T143022.dat"
        )

    def test_store_message_to_blob_custom_container_name(self):
        """Test storage with custom container name from settings"""
        message = {
            "id": "BSO_20240115T143022",
            "content": b"test message content",
            "bso_code": "BSO",
        }

        with patch(
            "manage_breast_screening.notifications.storage.azure.settings"
        ) as mock_settings:
            mock_settings.MESH_CONTAINER_NAME = "custom-mesh-container"

            fixed_dt = datetime(2024, 1, 15, 14, 30, 22)
            with patch(
                "manage_breast_screening.notifications.storage.azure.datetime"
            ) as mock_datetime:
                mock_datetime.now.return_value = fixed_dt

                store_message_to_blob(self.mock_blob_service_client, message)

                self.mock_blob_service_client.get_blob_client.assert_called_once_with(
                    container="custom-mesh-container",
                    blob="2024-01-15/BSO_20240115T143022.dat",
                )

    def test_store_message_to_blob_upload_failure(self):
        """Test storage fails when blob upload fails"""
        message = {
            "id": "BSO_20240115T143022",
            "content": b"test message content",
            "bso_code": "BSO",
        }

        # Mock upload failure
        self.mock_blob_client.upload_blob.side_effect = Exception("Upload failed")

        with self.assertRaises(Exception) as context:
            store_message_to_blob(self.mock_blob_service_client, message)

        self.assertIn("Upload failed", str(context.exception))
