from datetime import datetime

import pytest

from manage_breast_screening.notifications.management.commands.create_appointments import (
    TZ_INFO,
    Command,
)
from manage_breast_screening.notifications.models import Appointment, Clinic
from manage_breast_screening.notifications.services.blob_storage import BlobStorage
from manage_breast_screening.notifications.tests.integration.helpers import Helpers


@pytest.mark.integration
class TestCreateAppointmentsFromAzureStorage:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        monkeypatch.setenv(
            "BLOB_STORAGE_CONNECTION_STRING", Helpers().azurite_connection_string()
        )
        monkeypatch.setenv("BLOB_CONTAINER_NAME", "nbss-appoinments-data")

    @pytest.fixture
    def helpers(self):
        return Helpers()

    @pytest.mark.django_db
    def test_appointments_created_from_file_stored_in_azure(self, helpers):
        today_dirname = datetime.today().strftime("%Y-%m-%d")
        test_file_path = "ABC_20241202091221_APPT_106.dat"
        blob_name = f"{today_dirname}/{test_file_path}"

        with open(helpers.get_test_file_path(test_file_path)) as test_file:
            BlobStorage().add(blob_name, test_file.read())

        Command().handle(**{"date_str": today_dirname})

        assert Clinic.objects.count() == 2
        clinics = Clinic.objects.all()

        assert clinics[0].code == "BU003"
        assert clinics[0].bso_code == "KMK"
        assert clinics[0].holding_clinic is False
        assert clinics[0].name == "BREAST CARE UNIT"
        assert clinics[0].address_line_1 == "BREAST CARE UNIT"
        assert clinics[0].address_line_2 == "MILTON KEYNES HOSPITAL"
        assert clinics[0].address_line_3 == "STANDING WAY"
        assert clinics[0].address_line_4 == "MILTON KEYNES"
        assert clinics[0].address_line_5 == "MK6 5LD"
        assert clinics[0].postcode == "MK6 5LD"

        assert clinics[1].code == "BU011"
        assert clinics[1].bso_code == "KMK"
        assert clinics[1].holding_clinic is False
        assert clinics[1].name == "BREAST CARE UNIT"
        assert clinics[1].address_line_1 == "BREAST CARE UNIT"
        assert clinics[1].address_line_2 == "MILTON KEYNES HOSPITAL"
        assert clinics[1].address_line_3 == "STANDING WAY"
        assert clinics[1].address_line_4 == "MILTON KEYNES"
        assert clinics[1].address_line_5 == "MK6 5LD"
        assert clinics[1].postcode == "MK6 5LD"

        assert Appointment.objects.count() == 3
        appointments = Appointment.objects.all()

        assert appointments[0].nhs_number == 9449304424
        assert appointments[1].nhs_number == 9449305552
        assert appointments[2].nhs_number == 9449306621

        assert appointments[0].starts_at == datetime(2025, 1, 10, 8, 45, tzinfo=TZ_INFO)
        assert appointments[1].starts_at == datetime(
            2025, 3, 14, 13, 45, tzinfo=TZ_INFO
        )
        assert appointments[2].starts_at == datetime(
            2025, 3, 14, 14, 45, tzinfo=TZ_INFO
        )

        assert appointments[0].clinic == clinics[0]
        assert appointments[1].clinic == clinics[1]
        assert appointments[2].clinic == clinics[1]
