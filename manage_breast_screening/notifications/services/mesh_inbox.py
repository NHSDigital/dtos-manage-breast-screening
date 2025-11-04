import os
from tempfile import NamedTemporaryFile

from mesh_client import INT_ENDPOINT, LIVE_ENDPOINT, Endpoint, MeshClient, Message


class MeshInbox:
    def __init__(self):
        cert_file, private_key_file = self.ssl_credentials()
        self.client = MeshClient(
            self.endpoint_for_env(),
            mailbox=os.getenv("NBSS_MESH_INBOX_NAME"),
            password=os.getenv("NBSS_MESH_PASSWORD"),
            cert=(cert_file, private_key_file),
        )
        self.client.handshake()

    def fetch_message_ids(self) -> list[str]:
        return self.client.list_messages()

    def fetch_message(self, message_id: str) -> Message:
        return self.client.retrieve_message(message_id)

    def acknowledge(self, message_id: str):
        self.client.acknowledge_message(message_id)

    def endpoint_for_env(self) -> Endpoint:
        current_environment = os.getenv("DJANGO_ENV", "dev")
        if current_environment == "prod":
            return LIVE_ENDPOINT
        elif current_environment == "test":
            return Endpoint(os.getenv("NBSS_MESH_HOST"), None, None, False, False)
        else:
            return INT_ENDPOINT

    def __enter__(self):
        return self

    def __exit__(self, type_, value, tb):
        self.client.close()

    @classmethod
    def ssl_credentials(cls) -> tuple[NamedTemporaryFile]:
        cert = os.getenv("NBSS_MESH_CERT")
        private_key = os.getenv("NBSS_MESH_PRIVATE_KEY")

        return (
            cls.to_file(cert).name,
            cls.to_file(private_key).name,
        )

    @staticmethod
    def to_file(cert: str) -> NamedTemporaryFile:
        file = NamedTemporaryFile(delete=False)
        file.write(cert.encode("utf-8"))

        return file
