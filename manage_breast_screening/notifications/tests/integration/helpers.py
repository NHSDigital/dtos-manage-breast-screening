import os

from mesh_client import MeshClient


class Helpers:
    def add_file_to_mesh_mailbox(self, filepath: str):
        """Adds a file to MESH sandbox mailbox"""
        with open(filepath) as file:
            with MeshClient(
                url=os.getenv("NBSS_MESH_HOST", "http://localhost:8700"),
                mailbox=os.getenv("NBSS_MESH_INBOX_NAME", "X26ABC1"),
                password=os.getenv("NBSS_MESH_PASSWORD", "password"),
                shared_key=os.getenv("NBSS_MESH_SHARED_KEY", "TestKey"),
            ) as client:
                client.send_message(
                    os.getenv("NBSS_MESH_INBOX_NAME"),
                    file.read().encode("ASCII"),
                    filename=os.path.basename(filepath),
                    workflow_id="TEST_NBSS_WORKFLOW",
                )

    def get_test_file_path(self, test_file):
        return f"{os.path.dirname(os.path.realpath(__file__))}/../fixtures/{test_file}"

    def azurite_connection_string(self):
        """Default connection string for Azurite storage"""
        return (
            "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
            "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsu"  # gitleaks:allow
            "Fq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
            "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
            "QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;"
        )
