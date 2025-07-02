import datetime
import os
from unittest.mock import Mock, patch

import pytest
from azure.storage.blob import ContainerClient
from django.core.management.base import CommandError

from manage_breast_screening.notifications.management.commands.create_appointments import (
    Command,
)
from manage_breast_screening.notifications.models import Appointment, Clinic


@patch(
    (
        "manage_breast_screening.notifications."
        "management.commands.create_appointments."
        "BlobServiceClient"
    )
)
class TestCreateAppointments:
    @pytest.fixture
    def raw_data(self):
        return open(f"{os.path.dirname(os.path.realpath(__file__))}/test.dat").read()

    @pytest.mark.django_db
    def test_handle_creates_records(self, mock_blob_service, raw_data):
        """Test Appointment record creation from valid NBSS data stored in Azure storage blob"""
        today_dirname = datetime.datetime.today().strftime("%Y-%m-%d")

        subject = Command()

        mock_container_client = Mock(spec=ContainerClient)
        mock_container_client.list_blobs.return_value = [f"{today_dirname}/test.dat"]
        mock_container_client.get_blob_client().download_blob().readall.return_value = (
            raw_data
        )
        subject.container_client.return_value = mock_container_client

        subject.handle()

        assert len(Clinic.objects.all()) == 2
        assert len(Appointment.objects.all()) == 3

    @pytest.mark.django_db
    def test_handle_with_no_data(self, mock_blob_service):
        """Test that no records are created when there is no stored data"""
        subject = Command()
        mock_container_client = Mock(spec=ContainerClient)
        mock_container_client.list_blobs.return_value = []
        subject.container_client.return_value = mock_container_client

        subject.handle()

        assert len(Clinic.objects.all()) == 0
        assert len(Appointment.objects.all()) == 0

    def test_handle_with_error(self, mock_blob_service):
        """Test exception handling of the create_appointments command"""
        subject = Command()
        subject.container_client = Mock(side_effect=Exception("Oops"))

        with pytest.raises(CommandError):
            subject.handle()
