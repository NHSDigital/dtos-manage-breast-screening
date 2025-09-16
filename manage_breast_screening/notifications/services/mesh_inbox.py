import os
from tempfile import NamedTemporaryFile

from mesh_client import MeshClient, Message


class MeshInbox:
    def __init__(self):
        cert_file, private_key_file, ca_cert_file = self.ssl_credentials()
        self.client = MeshClient(
            url=os.getenv("NBSS_MESH_HOST"),
            mailbox=os.getenv("NBSS_MESH_INBOX_NAME"),
            password=os.getenv("NBSS_MESH_PASSWORD"),
            shared_key=os.getenv("NBSS_MESH_SHARED_KEY"),
            cert=(cert_file, private_key_file),
            verify=ca_cert_file,
        )
        self.client.handshake()

    def fetch_message_ids(self) -> list[str]:
        return self.client.list_messages()

    def fetch_message(self, message_id: str) -> Message:
        return self.client.retrieve_message(message_id)

    def acknowledge(self, message_id: str):
        self.client.acknowledge_message(message_id)

    def __enter__(self):
        return self

    def __exit__(self, type_, value, tb):
        self.client.close()

    @classmethod
    def ssl_credentials(cls) -> tuple[NamedTemporaryFile]:
        cert = os.getenv("NBSS_MESH_CERT")
        private_key = os.getenv("NBSS_MESH_PRIVATE_KEY")
        ca_cert = os.getenv("NBSS_MESH_CA_CERT")

        return (
            cls.to_file(cert).name,
            cls.to_file(private_key).name,
            cls.to_file(ca_cert).name,
        )

    @staticmethod
    def to_file(cert: str) -> NamedTemporaryFile:
        file = NamedTemporaryFile(delete=False)
        file.write(cert.encode("utf-8"))

        return file
