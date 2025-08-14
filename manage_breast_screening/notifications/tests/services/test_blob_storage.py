from unittest.mock import MagicMock, PropertyMock

import pytest
from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import (
    BlobClient,
    BlobServiceClient,
    ContainerClient,
    ContentSettings,
)

from manage_breast_screening.notifications.services.blob_storage import BlobStorage
from manage_breast_screening.notifications.tests.integration.helpers import Helpers


class TestBlobStorage:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        monkeypatch.setenv(
            "BLOB_STORAGE_CONNECTION_STRING", Helpers().azurite_connection_string()
        )
        monkeypatch.setenv("BLOB_CONTAINER_NAME", "test-container")

    def test_find_or_create_container_can_find_existing_container(self):
        """Test that the correct container is found when it already exists"""
        mock_service_client = PropertyMock(spec=BlobServiceClient)
        mock_service_client.create_container = PropertyMock(
            side_effect=ResourceExistsError("Error!")
        )

        subject = BlobStorage()
        subject.service_client = mock_service_client
        subject.find_or_create_container()

        mock_service_client.get_container_client.assert_called_once_with(
            "test-container"
        )

    def test_find_or_create_container_can_create_container(self):
        """Test that the correct container is found or created"""
        mock_service_client = PropertyMock(spec=BlobServiceClient)

        subject = BlobStorage()
        subject.service_client = mock_service_client
        subject.find_or_create_container()

        mock_service_client.create_container.assert_called_once_with("test-container")

    def test_add_blob_to_storage(self):
        """Test that the blob is added to the container"""

        mock_container_client = MagicMock(spec=ContainerClient)
        mock_blob_client = MagicMock(spec=BlobClient)
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
