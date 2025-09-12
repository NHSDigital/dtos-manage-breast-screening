import json

import pytest

from manage_breast_screening.notifications.management.commands.seed_clinics import (
    Command,
)
from manage_breast_screening.notifications.models import Clinic
from manage_breast_screening.notifications.tests.factories import (
    ClinicFactory,
)


class TestSeedClinics:
    @pytest.mark.django_db
    def test_seeds_new_valid_clinic_data(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _: "yes")
        assert len(Clinic.objects.all()) == 0

        seed_file = open(
            "./manage_breast_screening/notifications/data/clinic_data.json"
        ).read()
        json_data = json.loads(seed_file)

        Command().handle()

        all_clinics = Clinic.objects.all()
        assert len(all_clinics) == 22
        for index, clinic in enumerate(json_data):
            for key, value in clinic.items():
                assert str(getattr(all_clinics[index], key)) == value

    @pytest.mark.django_db
    def test_overwrites_location_data_on_existing_clinics(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _: "yes")

        seed_file = open(
            "./manage_breast_screening/notifications/data/clinic_data.json"
        ).read()
        json_data = json.loads(seed_file)

        existing_clinic = ClinicFactory(
            code=json_data[0]["code"],
            bso_code=json_data[0]["bso_code"],
            address_line_1="don't replace me",
            location_description="",
            location_url="",
        )

        Command().handle()

        existing_clinic.refresh_from_db()
        assert (
            existing_clinic.location_description == json_data[0]["location_description"]
        )
        assert existing_clinic.location_url == json_data[0]["location_url"]
        assert existing_clinic.address_line_1 == "don't replace me"
        all_clinics = Clinic.objects.all()
        assert len(all_clinics) == 22

    @pytest.mark.django_db
    def test_does_not_run_if_no_confirmation(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _: "no")

        seed_file = open(
            "./manage_breast_screening/notifications/data/clinic_data.json"
        ).read()
        json_data = json.loads(seed_file)

        existing_clinic = ClinicFactory(id=json_data[0]["id"], code="replace")
        assert len(Clinic.objects.all()) == 1

        Command().handle()

        assert len(Clinic.objects.all()) == 1
        existing_clinic.refresh_from_db()
        assert existing_clinic.code == "replace"
