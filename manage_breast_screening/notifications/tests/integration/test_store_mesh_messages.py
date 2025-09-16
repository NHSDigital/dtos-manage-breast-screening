import os
from datetime import datetime
from functools import cached_property

import pytest
from azure.storage.blob import BlobServiceClient, ContainerClient
from mesh_client import MeshClient

from manage_breast_screening.notifications.management.commands.store_mesh_messages import (
    Command,
)
from manage_breast_screening.notifications.tests.integration.helpers import Helpers


@pytest.mark.integration
class TestStoreMeshMessages:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
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

    @pytest.fixture
    def helpers(self):
        return Helpers()

    def test_retrieve_file(self, helpers):
        test_file_1 = helpers.get_test_file_path("ABC_20241202091221_APPT_106.dat")
        test_file_2 = helpers.get_test_file_path("ABC_20241202091321_APPT_107.dat")
        helpers.add_file_to_mesh_mailbox(test_file_1)
        helpers.add_file_to_mesh_mailbox(test_file_2)

        with MeshClient(
            url=os.getenv("NBSS_MESH_HOST"),
            mailbox=os.getenv("NBSS_MESH_INBOX_NAME"),
            password=os.getenv("NBSS_MESH_PASSWORD"),
            shared_key=os.getenv("NBSS_MESH_SHARED_KEY"),
        ) as client:
            assert len(client.list_messages()) == 2

            subject = Command()

            subject.handle()

            for blob in self.container_client.list_blobs():
                blob_client = self.container_client.get_blob_client(blob.name)
                blob_content = blob_client.download_blob(
                    max_concurrency=1, encoding="ASCII"
                ).readall()

                file_path, file_name = blob.name.split("/")

                assert file_path == datetime.today().strftime("%Y-%m-%d")

                file_path = helpers.get_test_file_path(file_name)

                with open(file_path) as test_file:
                    assert test_file.read() == blob_content

                self.container_client.delete_blob(blob.name)

            assert len(client.list_messages()) == 0

    @cached_property
    def container_client(self) -> ContainerClient:
        connection_string = os.getenv("BLOB_STORAGE_CONNECTION_STRING")
        container_name = os.getenv("BLOB_CONTAINER_NAME")

        return BlobServiceClient.from_connection_string(
            connection_string
        ).get_container_client(container_name)
