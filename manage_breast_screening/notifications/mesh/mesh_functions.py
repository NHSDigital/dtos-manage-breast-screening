import os

from mesh_client import MeshClient


def setup():
    client = MeshClient(
        url=os.getenv("MESH_BASE_URL"),
        mailbox=os.getenv("MESH_INBOX_NAME"),
        password=os.getenv("MESH_CLIENT_PASSWORD"),
        shared_key=os.getenv("MESH_CLIENT_SHARED_KEY"),
    )
    return client


def get_appointment_details(client: MeshClient, appointment_id: str) -> dict:
    appointment = client.retrieve_message(appointment_id)
    return appointment.read().decode("ASCII")
