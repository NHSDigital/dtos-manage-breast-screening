import datetime
import os
from unittest.mock import Mock, PropertyMock

import pytest
from azure.storage.blob import BlobProperties, ContainerClient
from django.core.management.base import CommandError

from manage_breast_screening.notifications.management.commands.create_appointments import (
    TZ_INFO,
    Command,
)
from manage_breast_screening.notifications.models import Appointment, Clinic


class TestCreateAppointments:
    @pytest.fixture
    def raw_data(self):
        return open(f"{os.path.dirname(os.path.realpath(__file__))}/test.dat").read()

    @pytest.mark.django_db
    def test_handle_creates_records(self, raw_data):
        """Test Appointment record creation from valid NBSS data stored in Azure storage blob"""
        today_dirname = datetime.datetime.today().strftime("%Y-%m-%d")

        subject = Command()

        mock_container_client = PropertyMock(spec=ContainerClient)
        mock_blob = Mock(spec=BlobProperties)
        mock_blob.name = PropertyMock(return_value=f"{today_dirname}/test.dat")
        mock_container_client.list_blobs.return_value = [mock_blob]
        mock_container_client.get_blob_client().download_blob().readall.return_value = (
            raw_data
        )
        subject.container_client = mock_container_client

        subject.handle(**{"date_str": today_dirname})

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

        assert Appointment.objects.count() == 3
        appointments = Appointment.objects.all()

        assert appointments[0].nhs_number == 9449304424
        assert appointments[1].nhs_number == 9449305552
        assert appointments[2].nhs_number == 9449306621

        assert appointments[0].starts_at == datetime.datetime(
            2025, 1, 10, 8, 45, tzinfo=TZ_INFO
        )
        assert appointments[1].starts_at == datetime.datetime(
            2025, 3, 14, 13, 45, tzinfo=TZ_INFO
        )
        assert appointments[2].starts_at == datetime.datetime(
            2025, 3, 14, 14, 45, tzinfo=TZ_INFO
        )

        assert appointments[0].status == "C"
        assert appointments[1].status == "B"
        assert appointments[2].status == "B"

        assert appointments[0].clinic == clinics[0]
        assert appointments[1].clinic == clinics[1]
        assert appointments[2].clinic == clinics[1]

    @pytest.mark.django_db
    def test_handle_accept_date_arg(self, raw_data):
        """Test Appointment record creation when passed a specific date as argument"""
        subject = Command()

        mock_container_client = PropertyMock(spec=ContainerClient)
        mock_blob = Mock(spec=BlobProperties)
        mock_blob.name = PropertyMock(return_value="2025-07-01/test.dat")
        mock_container_client.list_blobs.return_value = [mock_blob]
        mock_container_client.get_blob_client().download_blob().readall.return_value = (
            raw_data
        )
        subject.container_client = mock_container_client

        subject.handle(**{"date_str": "2025-07-01"})

        assert Clinic.objects.count() == 2
        assert Appointment.objects.count() == 3

    @pytest.mark.django_db
    def test_handle_with_invalid_date_arg(self):
        """Test command execution with an invalid date argument"""
        subject = Command()

        subject.container_client = PropertyMock(spec=ContainerClient)
        subject.container_client.list_blobs = Mock(side_effect=Exception("Error!"))

        with pytest.raises(CommandError):
            subject.handle("Noooooooo!")

        assert Appointment.objects.count() == 0

    @pytest.mark.django_db
    def test_handle_with_no_data(self):
        """Test that no records are created when there is no stored data"""
        subject = Command()
        mock_container_client = PropertyMock(spec=ContainerClient)
        mock_container_client.list_blobs.return_value = []
        subject.container_client = mock_container_client

        subject.handle(**{"date_str": "2000-01-01"})

        assert len(Clinic.objects.all()) == 0
        assert len(Appointment.objects.all()) == 0

    @pytest.mark.django_db
    def test_handle_with_error(self):
        """Test exception handling of the create_appointments command"""
        subject = Command()
        mock_container_client = PropertyMock(spec=ContainerClient)
        mock_container_client.list_blobs = Mock(side_effect=Exception("Oops"))
        subject.container_client = mock_container_client

        with pytest.raises(CommandError):
            subject.handle(**{"date_str": "2000-01-01"})

        assert Appointment.objects.count() == 0
