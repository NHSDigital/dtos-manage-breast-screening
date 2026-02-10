import logging
from datetime import datetime, timedelta
from os import getenv

import yaml
from django.core.management.base import BaseCommand
from django.test import override_settings

from manage_breast_screening.clinics.models import (
    Clinic,
    ClinicSlot,
    ClinicStatus,
    Provider,
    Setting,
    UserAssignment,
)
from manage_breast_screening.clinics.tests.factories import (
    ClinicFactory,
    ClinicSlotFactory,
    ProviderFactory,
    SettingFactory,
)
from manage_breast_screening.gateway.models import GatewayAction
from manage_breast_screening.manual_images.models import Series, Study
from manage_breast_screening.manual_images.tests.factories import (
    SeriesFactory,
    StudyFactory,
)
from manage_breast_screening.participants.models import (
    Appointment,
    AppointmentNote,
    AppointmentStatus,
    BenignLumpHistoryItem,
    BreastAugmentationHistoryItem,
    BreastCancerHistoryItem,
    CystHistoryItem,
    ImplantedMedicalDeviceHistoryItem,
    MastectomyOrLumpectomyHistoryItem,
    OtherProcedureHistoryItem,
    Participant,
    ParticipantAddress,
    ParticipantReportedMammogram,
    ScreeningEpisode,
)
from manage_breast_screening.participants.models.appointment import (
    AppointmentWorkflowStepCompletion,
)
from manage_breast_screening.participants.models.medical_information_review import (
    MedicalInformationReview,
)
from manage_breast_screening.participants.models.other_information.hormone_replacement_therapy import (
    HormoneReplacementTherapy,
)
from manage_breast_screening.participants.models.symptom import Symptom
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    AppointmentStatusFactory,
    BenignLumpHistoryItemFactory,
    BreastAugmentationHistoryItemFactory,
    BreastCancerHistoryItemFactory,
    CystHistoryItemFactory,
    ImplantedMedicalDeviceHistoryItemFactory,
    MastectomyOrLumpectomyHistoryItemFactory,
    OtherProcedureHistoryItemFactory,
    ParticipantAddressFactory,
    ParticipantFactory,
    ParticipantReportedMammogramFactory,
    ScreeningEpisodeFactory,
    SymptomFactory,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Seed demo data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--noinput", action="store_true", help="Do not prompt for confirmation"
        )

    def file_from_name(self, file_name):
        return open("manage_breast_screening/data/" + file_name)

    def handle(self, *args, **kwargs):
        if getenv("DJANGO_ENV", "production") == "production":
            raise Exception("This command cannot be run in production")

        if not kwargs["noinput"]:
            confirm = input(
                "You are about to delete everything and seed demo data. Are you sure? (yes/no)"
            )
            if confirm.strip().lower() != "yes":
                self.stdout.write(self.style.ERROR("Cancelled."))
                return

        # 🚩🚩🚩🚩🚩🚩🚩🚩🚩
        self.reset_db()
        # 🚩🚩🚩🚩🚩🚩🚩🚩🚩

        # silence all the timezone warnings
        with override_settings(USE_TZ=False):
            with self.file_from_name("demo_data.yml") as data_file:
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

        for file_key in setting_key["clinics"]:
            self.create_clinic(setting, file_key)

    def create_clinic(self, setting, file_key):
        with self.file_from_name(file_key["file"]) as data_file:
            clinic_data = yaml.safe_load(data_file)
            clinic_key = clinic_data["clinic"]

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
                name=status_key,
            )

        for symptom in appointment_key.get("symptoms", []):
            self.create_symptom(appointment, symptom)

        if "medical_information" in appointment_key:
            self.create_medical_information(
                appointment, appointment_key["medical_information"]
            )

        if "previous_mammograms" in appointment_key:
            self.create_reported_mammograms(
                appointment, appointment_key.get("previous_mammograms")
            )

        if "study" in appointment_key:
            self.create_study(appointment, appointment_key["study"])

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

    def create_medical_information(self, appointment, medical_information_key):
        for breast_cancer_history_item in medical_information_key.get(
            "breast_cancer_history_items", []
        ):
            self.create_breast_cancer_history_item(
                appointment, breast_cancer_history_item
            )
        for mastectomy_or_lumpectomy_history_item in medical_information_key.get(
            "mastectomy_or_lumpectomy_history_items", []
        ):
            self.create_mastectomy_or_lumpectomy_history_item(
                appointment, mastectomy_or_lumpectomy_history_item
            )

        for cyst_history_item in medical_information_key.get("cyst_history_items", []):
            self.create_cyst_history_item(appointment, cyst_history_item)

        for implanted_medical_device_history_item in medical_information_key.get(
            "implanted_medical_device_history_items", []
        ):
            self.create_implanted_medical_device_history_item(
                appointment, implanted_medical_device_history_item
            )

        for benign_lump_history_item in medical_information_key.get(
            "benign_lump_history_items", []
        ):
            self.create_benign_lump_history_item(appointment, benign_lump_history_item)

        for breast_augmentation_history_item in medical_information_key.get(
            "breast_augmentation_history_items", []
        ):
            self.create_breast_augmentation_history_item(
                appointment, breast_augmentation_history_item
            )

        for other_procedure_history_item in medical_information_key.get(
            "other_procedure_history_items", []
        ):
            self.create_other_procedure_history_item(
                appointment, other_procedure_history_item
            )

    def create_breast_cancer_history_item(
        self, appointment, breast_cancer_history_item
    ):
        BreastCancerHistoryItemFactory(
            appointment=appointment, **breast_cancer_history_item
        )

    def create_mastectomy_or_lumpectomy_history_item(
        self, appointment, mastectomy_or_lumpectomy_history_item
    ):
        MastectomyOrLumpectomyHistoryItemFactory(
            appointment=appointment, **mastectomy_or_lumpectomy_history_item
        )

    def create_cyst_history_item(self, appointment, cyst_history_item):
        CystHistoryItemFactory(appointment=appointment, **cyst_history_item)

    def create_implanted_medical_device_history_item(
        self, appointment, implanted_medical_device_history_item
    ):
        ImplantedMedicalDeviceHistoryItemFactory(
            appointment=appointment, **implanted_medical_device_history_item
        )

    def create_breast_augmentation_history_item(self, appointment, item):
        BreastAugmentationHistoryItemFactory(appointment=appointment, **item)

    def create_other_procedure_history_item(
        self, appointment, other_procedure_history_item
    ):
        OtherProcedureHistoryItemFactory(
            appointment=appointment, **other_procedure_history_item
        )

    def create_benign_lump_history_item(self, appointment, benign_lump_history_item):
        BenignLumpHistoryItemFactory(
            appointment=appointment, **benign_lump_history_item
        )

    def create_participant(self, **participant_key):
        address_key = participant_key.pop("address", None)
        participant = ParticipantFactory(**participant_key, address=None)

        if address_key is not None:
            ParticipantAddressFactory(**address_key, participant=participant)

        return participant

    def create_symptom(self, appointment, symptom):
        SymptomFactory(appointment=appointment, **symptom)

    def create_reported_mammograms(self, appointment, mammograms):
        for mammogram in mammograms:
            created_at_date = mammogram.pop("created_at", None)
            if mammogram["provider"] is not None:
                mammogram["provider"] = ProviderFactory(
                    id=mammogram["provider"]["id"],
                    name=mammogram["provider"]["name"],
                )
            appointment_mammogram = ParticipantReportedMammogramFactory(
                appointment=appointment,
                **mammogram,
            )
            if created_at_date is not None:
                appointment_mammogram.created_at = created_at_date
                appointment_mammogram.save()

            return appointment_mammogram

    def create_study(self, appointment, study_key):
        study = StudyFactory(
            id=study_key["id"],
            appointment=appointment,
            additional_details=study_key.get("additional_details", ""),
        )
        for series_key in study_key.get("series", []):
            SeriesFactory(
                id=series_key["id"],
                study=study,
                view_position=series_key["view_position"],
                laterality=series_key["laterality"],
                count=series_key.get("count", 1),
            )

    def reset_db(self):
        HormoneReplacementTherapy.objects.all().delete()
        AppointmentWorkflowStepCompletion.objects.all().delete()
        Series.objects.all().delete()
        Study.objects.all().delete()
        MedicalInformationReview.objects.all().delete()
        AppointmentNote.objects.all().delete()
        UserAssignment.objects.all().delete()
        Symptom.objects.all().delete()
        BreastAugmentationHistoryItem.objects.all().delete()
        BreastCancerHistoryItem.objects.all().delete()
        MastectomyOrLumpectomyHistoryItem.objects.all().delete()
        CystHistoryItem.objects.all().delete()
        ImplantedMedicalDeviceHistoryItem.objects.all().delete()
        OtherProcedureHistoryItem.objects.all().delete()
        BenignLumpHistoryItem.objects.all().delete()
        AppointmentStatus.objects.all().delete()
        ParticipantReportedMammogram.objects.all().delete()
        GatewayAction.objects.all().delete()
        Appointment.objects.all().delete()
        ScreeningEpisode.objects.all().delete()
        ParticipantAddress.objects.all().delete()
        Participant.objects.all().delete()
        ClinicSlot.objects.all().delete()
        ClinicStatus.objects.all().delete()
        Clinic.objects.all().delete()
        Setting.objects.all().delete()
        Provider.objects.all().delete()
