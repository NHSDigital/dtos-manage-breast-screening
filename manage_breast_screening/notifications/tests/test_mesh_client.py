# Create your tests here.


import pytest
from mesh_client import MeshClient

base_uri = "http://localhost:8700"  # Replace with your actual base URI
_CANNED_MAILBOX1 = "X26ABC1"
_PASSWORD = "Password"
_SHARED_KEY = "Testkey"


@pytest.mark.skip(
    reason="This test depends on mesh-sandbox running in another container"
)
def test_get_file():
    with MeshClient(
        url=base_uri,
        mailbox=_CANNED_MAILBOX1,
        password=_PASSWORD,
        shared_key=_SHARED_KEY,
    ) as client:
        client.handshake()
        message_ids = client.list_messages()
        assert len(message_ids) == 1

        assert message_ids[0] == "SIMPLE_MESSAGE"
        message = client.retrieve_message(message_ids[0]).read().decode("utf-8")

        assert message.startswith(
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
        )
        assert message.endswith(
            "Pellentesque eget nisi eu ex ullamcorper ultricies molestie ut lorem."
        )
