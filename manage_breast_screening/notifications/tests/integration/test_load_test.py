import os
from datetime import datetime

import pytest

from manage_breast_screening.notifications.management.commands.create_appointments import (
    Command,
)
from manage_breast_screening.notifications.services.blob_storage import BlobStorage
from manage_breast_screening.notifications.tests.integration.helpers import Helpers
from scripts.python.load_test.notifications_load_test import generate_load_test_data


# TODO: DELETE - setup as easy way to validate data locally
@pytest.mark.integration
class TestLoadTest:
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
    def test_generate_test_data(self, helpers):
        for number in range(10):
            with open(
                f"{os.path.dirname(os.path.realpath(__file__))}/../fixtures/load_data_{number}.dat",
                "w",
            ) as file:
                data_string = generate_load_test_data(number)
                file.write(data_string)

        for number in range(10):
            today_dirname = datetime.today().strftime("%Y-%m-%d")
            test_file_name = f"load_data_{number}.dat"
            blob_name = f"{today_dirname}/{test_file_name}"

            with open(
                f"{os.path.dirname(os.path.realpath(__file__))}/../fixtures/load_data_{number}.dat"
            ) as test_file:
                BlobStorage().add(blob_name, test_file.read())

            Command().handle(**{"date_str": today_dirname})
