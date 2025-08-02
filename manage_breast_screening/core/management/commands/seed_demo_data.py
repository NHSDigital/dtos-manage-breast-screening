import logging
from datetime import datetime, timedelta

import yaml
from django.core.management.base import BaseCommand

from manage_breast_screening.clinics.models import (
    Clinic,
    ClinicSlot,
    ClinicStatus,
    Provider,
    Setting,
)
from manage_breast_screening.clinics.tests.factories import (
    ClinicFactory,
    ProviderFactory,
    SettingFactory,
)
from manage_breast_screening.participants.models import (
    Appointment,
    AppointmentStatus,
    Participant,
    ParticipantAddress,
    ScreeningEpisode,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Seed demo data"

    def handle(self, *args, **kwargs):
        # TODO guard against runnning in production
        self.reset_db()
        with open("manage_breast_screening/data/demo_data.yml", "r") as data_file:
            data = yaml.safe_load(data_file)
            for provider_key in data["providers"]:
                self.create_provider(provider_key)

    def create_provider(self, provider_key):
        provider = ProviderFactory(name=provider_key["name"], id=provider_key["id"])
        for setting_key in provider_key["settings"]:
            self.create_setting(provider, setting_key)

    def create_setting(self, provider, setting_key):
        setting = SettingFactory(
            name=setting_key["name"], id=setting_key["id"], provider=provider
        )
        for clinic_key in setting_key["clinics"]:
            self.create_clinic(setting, clinic_key)

    def create_clinic(self, setting, clinic_key):
        starts_at = datetime.now() + timedelta(
            days=clinic_key["starts_at_date_relative_to_today_in_days"]
        )
        starts_at = datetime.combine(
            starts_at.date(),
            datetime.strptime(clinic_key["starts_at_time"], "%H:%M").time(),
        )
        ends_at = datetime.combine(
            starts_at.date(),
            datetime.strptime(clinic_key["ends_at_time"], "%H:%M").time(),
        )

        ClinicFactory(
            setting=setting, id=clinic_key["id"], starts_at=starts_at, ends_at=ends_at
        )

    def reset_db(self):
        AppointmentStatus.objects.all().delete()
        Appointment.objects.all().delete()
        ScreeningEpisode.objects.all().delete()
        ParticipantAddress.objects.all().delete()
        Participant.objects.all().delete()
        ClinicSlot.objects.all().delete()
        ClinicStatus.objects.all().delete()
        Clinic.objects.all().delete()
        Setting.objects.all().delete()
        Provider.objects.all().delete()
