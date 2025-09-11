from unittest.mock import MagicMock, patch

import pytest
from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import (
    BlobClient,
    ContainerClient,
    ContentSettings,
)

from manage_breast_screening.notifications.services.blob_storage import BlobStorage
from manage_breast_screening.notifications.tests.integration.helpers import Helpers


@patch("manage_breast_screening.notifications.services.blob_storage.BlobServiceClient")
class TestBlobStorage:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        monkeypatch.setenv(
            "BLOB_STORAGE_CONNECTION_STRING", Helpers().azurite_connection_string()
        )
        monkeypatch.setenv("BLOB_CONTAINER_NAME", "test-container")

    def test_find_or_create_container_can_find_existing_container(
        self, mock_blob_client
    ):
        """Test that the correct container is found when it already exists"""
        mock_blob_client.create_container.side_effect = ResourceExistsError("Error!")

        subject = BlobStorage()
        subject.client = mock_blob_client
        subject.find_or_create_container("test-container")

        mock_blob_client.get_container_client.assert_called_once_with("test-container")

    def test_find_or_create_container_can_create_container(self, mock_blob_client):
        """Test that the correct container is found or created"""
        subject = BlobStorage()
        subject.client = mock_blob_client
        subject.find_or_create_container("test-container")

        mock_blob_client.create_container.assert_called_once_with("test-container")

    def test_add_blob_to_storage(self, mock_blob_client):
        """Test that the blob is added to the container"""
        mock_container_client = MagicMock(spec=ContainerClient)
        mock_container_client.get_blob_client.return_value = mock_blob_client

        subject = BlobStorage()
        subject.find_or_create_container = MagicMock(return_value=mock_container_client)
        subject.add("test-blob", "test-content")

        mock_container_client.get_blob_client.assert_called_once_with("test-blob")
        mock_blob_client.upload_blob.assert_called_once_with(
            "test-content",
            blob_type="BlockBlob",
            content_settings=ContentSettings(
                content_type="application/dat", content_encoding="ASCII"
            ),
            overwrite=True,
        )

    def test_add_blob_to_storage_with_additional_args(self, mock_blob_client):
        """Test that the blob is added to the specified container with the correct content type"""

        mock_container_client = MagicMock(spec=ContainerClient)
        mock_blob_client = MagicMock(spec=BlobClient)
        mock_container_client.get_blob_client.return_value = mock_blob_client

        subject = BlobStorage()
        subject.find_or_create_container = MagicMock(return_value=mock_container_client)
        subject.add(
            "test-blob.csv",
            "test,content",
            content_type="text/csv",
            container_name="test-csv-container",
        )

        subject.find_or_create_container.assert_called_once_with("test-csv-container")
        mock_container_client.get_blob_client.assert_called_once_with("test-blob.csv")
        mock_blob_client.upload_blob.assert_called_once_with(
            "test,content",
            blob_type="BlockBlob",
            content_settings=ContentSettings(
                content_type="text/csv", content_encoding="ASCII"
            ),
            overwrite=True,
        )

    def test_blob_storage_initialises_using_managed_identity_credentials(
        self, mock_blob_client, monkeypatch
    ):
        monkeypatch.setenv("STORAGE_ACCOUNT_NAME", "mystorageaccount")
        monkeypatch.setenv("BLOB_MI_CLIENT_ID", "my-mi-id")
        mock_mi_cred = MagicMock()

        with patch(
            "manage_breast_screening.notifications.services.blob_storage.BlobServiceClient"
        ) as blob_client:
            with patch(
                "manage_breast_screening.notifications.services.blob_storage.ManagedIdentityCredential"
            ) as managed_identity_constructor:
                managed_identity_constructor.return_value = mock_mi_cred

                BlobStorage()

                blob_client.assert_called_once_with(
                    "https://mystorageaccount.blob.core.windows.net",
                    credential=mock_mi_cred,
                )
                managed_identity_constructor.assert_called_once_with(
                    client_id="my-mi-id"
                )
