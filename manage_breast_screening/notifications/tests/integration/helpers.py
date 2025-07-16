import os
from typing import Any

from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient, ContainerClient, ContentSettings
from mesh_client import MeshClient


class Helpers:
    def find_or_create_blob_container(self) -> ContainerClient:
        """Find or create an Azure Storage Blob container"""

        connection_string = os.getenv("BLOB_STORAGE_CONNECTION_STRING")
        container_name = os.getenv("BLOB_CONTAINER_NAME")

        service_client = BlobServiceClient.from_connection_string(connection_string)

        try:
            return service_client.create_container(container_name)
        except ResourceExistsError:
            return service_client.get_container_client(container_name)

    def add_to_blob_storage(
        self,
        filename: str,
        content: str,
        content_encoding="ASCII",
        content_type="application/dat",
    ) -> dict[str, Any]:
        """Write a file to the configured blob container"""

        container = self.find_or_create_blob_container()
        blob_client = container.get_blob_client(filename)
        return blob_client.upload_blob(
            content,
            blob_type="BlockBlob",
            content_settings=ContentSettings(
                content_type=content_type, content_encoding=content_encoding
            ),
            overwrite=True,
        )

    def add_file_to_mesh_mailbox(self, filepath: str):
        """Adds a file to MESH sandbox mailbox"""
        with open(filepath) as file:
            with MeshClient(
                url=os.getenv("MESH_BASE_URL", "http://localhost:8700"),
                mailbox=os.getenv("MESH_INBOX_NAME", "X26ABC1"),
                password=os.getenv("MESH_CLIENT_PASSWORD", "password"),
                shared_key=os.getenv("MESH_CLIENT_SHARED_KEY", "TestKey"),
            ) as client:
                client.send_message(
                    os.getenv("MESH_INBOX_NAME"),
                    file.read().encode("ASCII"),
                    filename=os.path.basename(filepath),
                    workflow_id="TEST_NBSS_WORKFLOW",
                )

    def test_dat_file_path(self):
        return (
            f"{os.path.dirname(os.path.realpath(__file__))}"
            "/../management/commands/test.dat"
        )

    def azurite_connection_string(self):
        """Default connection string for Azurite storage"""
        return (
            "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
            "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsu"  # gitleaks:allow
            "Fq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
            "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
        )
