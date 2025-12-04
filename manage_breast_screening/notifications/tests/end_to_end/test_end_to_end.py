import os
from datetime import datetime, timedelta

import pytest
from django.test import TestCase
from test.support.os_helper import EnvironmentVarGuard

from manage_breast_screening.notifications.management.commands.create_appointments import (
    Command as CreateAppointments,
)
from manage_breast_screening.notifications.management.commands.store_mesh_messages import (
    Command as StoreMeshMessages,
)
from manage_breast_screening.notifications.models import (
    Appointment,
)
from manage_breast_screening.notifications.tests.integration.helpers import Helpers


class TestEndToEnd(TestCase):
    @pytest.fixture(autouse=True)
    def setup_environment(self):
        connection_string = Helpers().azurite_connection_string()
        self.env = EnvironmentVarGuard()
        self.env.set("DJANGO_ENV", "test")
        self.env.set("NBSS_MESH_HOST", "http://localhost:8700")
        self.env.set("NBSS_MESH_PASSWORD", "password")
        self.env.set("NBSS_MESH_SHARED_KEY", "TestKey")
        self.env.set("NBSS_MESH_INBOX_NAME", "X26ABC1")
        self.env.set("NBSS_MESH_CERT", "mesh-cert")
        self.env.set("NBSS_MESH_PRIVATE_KEY", "mesh-private-key")
        self.env.set("NBSS_MESH_CA_CERT", "mesh-ca-cert")
        self.env.set("BLOB_STORAGE_CONNECTION_STRING", connection_string)
        self.env.set("QUEUE_STORAGE_CONNECTION_STRING", connection_string)
        self.env.set("BLOB_CONTAINER_NAME", "nbss-appoinments-data")

        Helpers().add_file_to_mesh_mailbox(
            f"{os.path.dirname(os.path.realpath(__file__))}/ABC_20250302091221_APPT_100.dat"
        )

    @pytest.mark.django_db
    def test_all_commands_in_sequence(self):
        StoreMeshMessages().handle()

        today_dirname = datetime.today().strftime("%Y-%m-%d")
        CreateAppointments().handle(**{"date_str": today_dirname})

        appointments = Appointment.objects.filter(
            episode_type__in=["F", "G", "R", "S"],
            starts_at__lte=datetime.now() + timedelta(weeks=4),
            status="B",
            number="1",
        )

        appointment_date = datetime.now() + timedelta(days=2)
        appointments.update(starts_at=appointment_date)

        assert appointments.count() == 3
