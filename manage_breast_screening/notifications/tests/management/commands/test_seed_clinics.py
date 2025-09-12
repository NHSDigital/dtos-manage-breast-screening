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
    def test_overwrites_existing_clinics(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _: "yes")

        seed_file = open(
            "./manage_breast_screening/notifications/data/clinic_data.json"
        ).read()
        json_data = json.loads(seed_file)

        existing_clinic = ClinicFactory(id=json_data[0]["id"], code="replace")

        Command().handle()

        existing_clinic.refresh_from_db()
        assert existing_clinic.code == json_data[0]["code"]
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
