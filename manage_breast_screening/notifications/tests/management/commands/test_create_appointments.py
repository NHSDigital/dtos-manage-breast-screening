import os
from datetime import datetime, timezone
from unittest.mock import Mock, PropertyMock, patch

import pytest
from azure.storage.blob import BlobProperties
from django.core.management.base import CommandError

from manage_breast_screening.notifications.management.commands.create_appointments import (
    TZ_INFO,
    Command,
)
from manage_breast_screening.notifications.models import Appointment, Clinic
from manage_breast_screening.notifications.tests.factories import (
    AppointmentFactory,
    ClinicFactory,
)

VALID_DATA_FILE = "ABC_20241202091221_APPT_106.dat"
UPDATED_APPOINTMENT_FILE = "ABC_20241202091321_APPT_107.dat"
HOLDING_CLINIC_APPOINTMENT_FILE = "ABC_20241202091421_APPT_108.dat"
COMPLETED_APPOINTMENT_FILE = "ABC_20241202091521_APPT_109.dat"


@patch(
    "manage_breast_screening.notifications.management.commands.create_appointments.BlobStorage"
)
@pytest.mark.django_db
class TestCreateAppointments:
    def fixture_file_path(self, filename):
        return (
            f"{os.path.dirname(os.path.realpath(__file__))}/../../fixtures/{filename}"
        )

    def test_handle_creates_records(self, mock_blob_storage):
        """Test Appointment creation for new booked appointments in NBSS data, stored in Azure storage blob"""
        today_dirname = datetime.today().strftime("%Y-%m-%d")

        mock_container_client = (
            mock_blob_storage.return_value.find_or_create_container.return_value
        )
        mock_blob = Mock(spec=BlobProperties)
        mock_blob.name = PropertyMock(return_value=f"{today_dirname}/{VALID_DATA_FILE}")
        mock_container_client.list_blobs.return_value = [mock_blob]
        mock_container_client.get_blob_client().download_blob().readall.return_value = (
            open(self.fixture_file_path(VALID_DATA_FILE)).read()
        )

        Command().handle(**{"date_str": today_dirname})

        assert Clinic.objects.count() == 2
        clinics = Clinic.objects.all()

        assert clinics[0].code == "BU003"
        assert clinics[1].code == "BU011"
        assert clinics[0].bso_code == "KMK"
        assert clinics[0].holding_clinic is False
        assert clinics[0].name == "BREAST CARE UNIT"
        assert clinics[0].address_line_1 == "BREAST CARE UNIT"
        assert clinics[0].address_line_2 == "MILTON KEYNES HOSPITAL"
        assert clinics[0].address_line_3 == "STANDING WAY"
        assert clinics[0].address_line_4 == "MILTON KEYNES"
        assert clinics[0].address_line_5 == "MK6 5LD"
        assert clinics[0].postcode == "MK6 5LD"

        assert Appointment.objects.count() == 2
        appointments = Appointment.objects.all()

        assert appointments[0].nhs_number == 9449305552
        assert appointments[1].nhs_number == 9449306621

        assert appointments[0].starts_at == datetime(
            2025, 3, 14, 13, 45, tzinfo=TZ_INFO
        )
        assert appointments[1].starts_at == datetime(
            2025, 3, 14, 14, 45, tzinfo=TZ_INFO
        )

        assert appointments[0].status == "B"
        assert appointments[1].status == "B"

        assert appointments[0].batch_id == "KMK001326"
        assert appointments[1].batch_id == "KMK001326"

        assert appointments[0].episode_type == "S"
        assert appointments[1].episode_type == "F"

        assert appointments[0].booked_by == "H"
        assert appointments[0].booked_at == datetime.strptime(
            "20250128-154003", "%Y%m%d-%H%M%S"
        ).replace(tzinfo=TZ_INFO)
        assert appointments[1].booked_by == "H"
        assert appointments[1].booked_at == datetime.strptime(
            "20250128-154004", "%Y%m%d-%H%M%S"
        ).replace(tzinfo=TZ_INFO)

        assert appointments[0].clinic == clinics[1]
        assert appointments[1].clinic == clinics[1]

        assert appointments[1].assessment is True

    def test_handles_holding_clinics(self, mock_blob_storage):
        """Test does not create appointments for valid NBSS data marked as a Holding Clinic"""
        today_dirname = datetime.today().strftime("%Y-%m-%d")

        mock_container_client = (
            mock_blob_storage.return_value.find_or_create_container.return_value
        )
        mock_blob = Mock(spec=BlobProperties)
        mock_blob.name = PropertyMock(
            return_value=f"{today_dirname}/{HOLDING_CLINIC_APPOINTMENT_FILE}"
        )
        mock_container_client.list_blobs.return_value = [mock_blob]
        mock_container_client.get_blob_client().download_blob().readall.return_value = (
            open(self.fixture_file_path(HOLDING_CLINIC_APPOINTMENT_FILE)).read()
        )

        Command().handle(**{"date_str": today_dirname})

        assert Clinic.objects.count() == 1
        assert Clinic.objects.filter(code="BU011").first() is None

        assert Clinic.objects.count() == 1
        assert Appointment.objects.filter(nhs_number=9449306625).first() is None

    def test_does_not_save_cancellations_for_new_appointments(self, mock_blob_storage):
        """Test no new Appointment created if the data shows Cancelled status"""
        today = datetime.now()
        raw_data = open(self.fixture_file_path(UPDATED_APPOINTMENT_FILE)).read()
        today_dirname = today.strftime("%Y-%m-%d")

        mock_container_client = (
            mock_blob_storage.return_value.find_or_create_container.return_value
        )
        mock_blob = Mock(spec=BlobProperties)
        mock_blob.name = PropertyMock(
            return_value=f"{today_dirname}/{UPDATED_APPOINTMENT_FILE}"
        )
        mock_container_client.list_blobs.return_value = [mock_blob]
        mock_container_client.get_blob_client().download_blob().readall.return_value = (
            raw_data
        )

        Command().handle(**{"date_str": today_dirname})

        assert Appointment.objects.count() == 0

    def test_handle_updates_records(self, mock_blob_storage):
        """Test Appointment record update from valid NBSS data stored in Azure storage blob"""
        starts_at = datetime.strptime(
            "20250314 1345",
            "%Y%m%d %H%M",
        )
        nbss_id = "BU011-67278-RA1-DN-Y1111-1"
        # Setup existing appointment
        existing_appointment = AppointmentFactory(
            nbss_id=nbss_id,
            nhs_number=9449305552,
            starts_at=starts_at.replace(tzinfo=TZ_INFO),
            clinic=ClinicFactory(
                bso_code="KMK",
                code="BU011",
            ),
            status="B",
            cancelled_by="",
        )
        assert Appointment.objects.count() == 1

        # Receive a cancellation for existing appointment
        today = datetime.now()
        raw_data = open(self.fixture_file_path(UPDATED_APPOINTMENT_FILE)).read()
        today_dirname = today.strftime("%Y-%m-%d")

        mock_container_client = (
            mock_blob_storage.return_value.find_or_create_container.return_value
        )
        mock_blob = Mock(spec=BlobProperties)
        mock_blob.name = PropertyMock(
            return_value=f"{today_dirname}/{UPDATED_APPOINTMENT_FILE}"
        )
        mock_container_client.list_blobs.return_value = [mock_blob]
        mock_container_client.get_blob_client().download_blob().readall.return_value = (
            raw_data
        )

        Command().handle(**{"date_str": today_dirname})

        # check existing appointment updated
        assert Appointment.objects.count() == 1
        appointments = Appointment.objects.all()
        assert appointments[0].id == existing_appointment.id
        assert appointments[0].nbss_id == nbss_id
        assert appointments[0].status == "C"
        assert appointments[0].cancelled_by == "C"
        assert appointments[0].cancelled_at == datetime.strptime(
            "20250128-154003", "%Y%m%d-%H%M%S"
        ).replace(tzinfo=TZ_INFO)

    def test_only_updates_cancelled_appointments(self, mock_blob_storage):
        """We should not update Appointments unless its a Cancellation"""

        starts_at = datetime.strptime(
            "20250314 1345",
            "%Y%m%d %H%M",
        )
        nbss_id_no_update = "BU011-67278-RA1-DN-Y1111-1"
        today = datetime.now()
        today_dirname = today.strftime("%Y-%m-%d")
        blob_name = f"{today_dirname}/{VALID_DATA_FILE}"

        existing_appt_no_update = AppointmentFactory(
            nbss_id=nbss_id_no_update,
            nhs_number=9449305552,
            starts_at=starts_at.replace(tzinfo=TZ_INFO),
            clinic=ClinicFactory(
                bso_code="KMK",
                code="BU011",
            ),
            status="C",
        )

        nbss_id_cancelled = "BU003-67215-RA1-DN-Z2222-1"
        existing_appt_to_cancel = AppointmentFactory(
            nbss_id=nbss_id_cancelled,
            nhs_number=9449304424,
            starts_at=starts_at.replace(tzinfo=TZ_INFO),
            clinic=ClinicFactory(
                bso_code="KMK",
                code="BU003",
            ),
            status="B",
        )

        raw_data = open(self.fixture_file_path(VALID_DATA_FILE)).read()

        mock_container_client = (
            mock_blob_storage.return_value.find_or_create_container.return_value
        )
        mock_blob = Mock(spec=BlobProperties)
        mock_blob.name = blob_name
        mock_container_client.list_blobs.return_value = [mock_blob]
        mock_container_client.get_blob_client().download_blob().readall.return_value = (
            raw_data
        )

        Command().handle(**{"date_str": today_dirname})

        # has not been updated with test file data
        assert (
            Appointment.objects.filter(id=existing_appt_no_update.id)[0].status == "C"
        )
        # has been cancelled from test file data
        assert (
            Appointment.objects.filter(id=existing_appt_to_cancel.id)[0].status == "C"
        )

    def test_creates_completed_appointments(self, mock_blob_storage):
        today_dirname = datetime.today().strftime("%Y-%m-%d")
        mock_container_client = (
            mock_blob_storage.return_value.find_or_create_container.return_value
        )
        mock_blob = Mock(spec=BlobProperties)
        mock_blob.name = PropertyMock(
            return_value=f"{today_dirname}/{COMPLETED_APPOINTMENT_FILE}"
        )
        mock_container_client.list_blobs.return_value = [mock_blob]
        mock_container_client.get_blob_client().download_blob().readall.return_value = (
            open(self.fixture_file_path(COMPLETED_APPOINTMENT_FILE)).read()
        )

        clinic = ClinicFactory(bso_code="KMK", code="BU003")
        booked_appt1 = AppointmentFactory(
            nbss_id="BU011-67278-RA1-DN-Y1111-1",
            nhs_number=9449305552,
            starts_at=datetime(2025, 3, 14, 13, 45, tzinfo=TZ_INFO),
            clinic=clinic,
            status="B",
        )

        booked_appt2 = AppointmentFactory(
            nbss_id="BU011-67278-RA1-DN-X0000-1",
            nhs_number=9449306621,
            starts_at=datetime(2025, 3, 14, 14, 45, tzinfo=TZ_INFO),
            clinic=clinic,
            status="B",
        )

        Command().handle(**{"date_str": today_dirname})

        booked_appt1.refresh_from_db()
        booked_appt2.refresh_from_db()

        assert booked_appt1.status == "A"
        assert booked_appt1.completed_at == datetime(
            2025, 1, 28, 15, 40, 3, tzinfo=timezone.utc
        )
        assert booked_appt1.attended_not_screened == "N"

        assert booked_appt2.status == "D"
        assert booked_appt2.completed_at == datetime(
            2025, 1, 28, 15, 40, 4, tzinfo=timezone.utc
        )
        assert booked_appt2.attended_not_screened == ""

    def test_handle_accept_date_arg(self, mock_blob_storage):
        """Test Appointment record creation when passed a specific date as argument"""
        mock_container_client = (
            mock_blob_storage.return_value.find_or_create_container.return_value
        )
        mock_blob = Mock(spec=BlobProperties)
        mock_blob.name = PropertyMock(return_value=f"2025-07-01/{VALID_DATA_FILE}")
        mock_container_client.list_blobs.return_value = [mock_blob]
        mock_container_client.get_blob_client().download_blob().readall.return_value = (
            open(self.fixture_file_path(VALID_DATA_FILE)).read()
        )

        Command().handle(**{"date_str": "2025-07-01"})

        assert Clinic.objects.count() == 2
        assert Appointment.objects.count() == 2

    def test_handle_with_invalid_date_arg(self, mock_blob_storage):
        """Test command execution with an invalid date argument"""
        mock_container_client = (
            mock_blob_storage.return_value.find_or_create_container.return_value
        )
        mock_container_client.list_blobs = Mock(side_effect=Exception("Error!"))

        with pytest.raises(CommandError):
            Command().handle(**{"date_str": "Noooo!"})

        assert Appointment.objects.count() == 0

    def test_handle_with_no_data(self, mock_blob_storage):
        """Test that no records are created when there is no stored data"""
        mock_container_client = (
            mock_blob_storage.return_value.find_or_create_container.return_value
        )
        mock_container_client.list_blobs.return_value = []

        Command().handle(**{"date_str": "2000-01-01"})

        assert len(Clinic.objects.all()) == 0
        assert len(Appointment.objects.all()) == 0

    def test_handle_with_error(self, mock_blob_storage):
        """Test exception handling of the create_appointments command"""
        mock_container_client = (
            mock_blob_storage.return_value.find_or_create_container.return_value
        )
        mock_container_client.list_blobs = Mock(side_effect=Exception("Oops"))

        with pytest.raises(CommandError):
            Command().handle(**{"date_str": "2000-01-01"})

        assert Appointment.objects.count() == 0
