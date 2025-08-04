import logging
from datetime import datetime, timedelta

import yaml
from django.conf import settings
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
    ClinicSlotFactory,
    ProviderFactory,
    SettingFactory,
)
from manage_breast_screening.participants.models import (
    Appointment,
    AppointmentStatus,
    Participant,
    ParticipantAddress,
    ParticipantReportedMammogram,
    ScreeningEpisode,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    AppointmentStatusFactory,
    ParticipantAddressFactory,
    ParticipantFactory,
    ParticipantReportedMammogramFactory,
    ScreeningEpisodeFactory,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Seed demo data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--noinput", action="store_true", help="Do not prompt for confirmation"
        )

    def handle(self, *args, **kwargs):
        if settings.DEBUG is False:
            raise Exception("This command cannot be run in production")

        if not kwargs["noinput"]:
            confirm = input(
                "You are about to delete everything and seed demo data. Are you sure? (yes/no)"
            )
            if confirm.strip().lower() != "yes":
                self.stdout.write(self.style.ERROR("Cancelled."))
                return

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
        current_status = clinic_key.get("status", ClinicStatus.SCHEDULED)

        clinic = ClinicFactory(
            setting=setting,
            id=clinic_key["id"],
            starts_at=starts_at,
            ends_at=ends_at,
            current_status=current_status,
        )

        slots = clinic_key.get("slots")
        if slots:
            for slot_key in slots:
                self.create_slot(clinic, slot_key)

    def create_slot(self, clinic, slot_key):
        starts_at = datetime.combine(
            clinic.starts_at.date(),
            datetime.strptime(slot_key["starts_at_time"], "%H:%M").time(),
        )

        clinic_slot = ClinicSlotFactory(
            clinic=clinic,
            id=slot_key["id"],
            duration_in_minutes=slot_key["duration_in_minutes"],
            starts_at=starts_at,
        )

        if "appointment" in slot_key:
            self.create_appointment(clinic_slot, slot_key["appointment"])

    def create_appointment(self, clinic_slot, appointment_key):
        if "screening_episode" in appointment_key:
            screening_episode = self.create_screening_episode(
                appointment_key["screening_episode"]
            )

        appointment = AppointmentFactory(
            clinic_slot=clinic_slot,
            id=appointment_key["id"],
            screening_episode=screening_episode,
        )

        for status_key in appointment_key.get("statuses", []):
            AppointmentStatusFactory(
                appointment=appointment,
                state=status_key,
            )

        return appointment

    def create_screening_episode(self, screening_episode_key):
        if "participant" in screening_episode_key:
            participant = self.create_participant(
                **screening_episode_key["participant"]
            )

        return ScreeningEpisodeFactory(
            id=screening_episode_key["id"],
            participant=participant,
        )

    def create_participant(self, **participant_key):
        address_key = participant_key.pop("address", None)
        previous_mammograms_key = participant_key.pop("previous_mammograms", [])
        participant = ParticipantFactory(**participant_key, address=None)

        if address_key is not None:
            ParticipantAddressFactory(**address_key, participant=participant)

        self.create_reported_mammograms(participant, previous_mammograms_key)
        return participant

    def create_reported_mammograms(self, participant, mammograms):
        for mammogram in mammograms:
            if mammogram["provider"] is not None:
                mammogram["provider"] = ProviderFactory(
                    id=mammogram["provider"]["id"],
                    name=mammogram["provider"]["name"],
                )
            ParticipantReportedMammogramFactory(
                participant=participant,
                **mammogram,
            )

    def reset_db(self):
        AppointmentStatus.objects.all().delete()
        Appointment.objects.all().delete()
        ParticipantReportedMammogram.objects.all().delete()
        ScreeningEpisode.objects.all().delete()
        ParticipantAddress.objects.all().delete()
        Participant.objects.all().delete()
        ClinicSlot.objects.all().delete()
        ClinicStatus.objects.all().delete()
        Clinic.objects.all().delete()
        Setting.objects.all().delete()
        Provider.objects.all().delete()
