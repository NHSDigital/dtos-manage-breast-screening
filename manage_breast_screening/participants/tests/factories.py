from datetime import date

from factory import Faker, post_generation
from factory.declarations import (
    Iterator,
    LazyAttribute,
    LazyFunction,
    RelatedFactory,
    Sequence,
    SubFactory,
    Trait,
)
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice

from manage_breast_screening.auth.tests.factories import UserFactory
from manage_breast_screening.clinics.tests.factories import (
    ClinicSlotFactory,
    ProviderFactory,
)
from manage_breast_screening.participants.models import (
    BreastCancerHistoryItem,
    MastectomyOrLumpectomyHistoryItem,
    BenignLumpHistoryItem,
    BreastCancerHistoryItem,
    ImplantedMedicalDeviceHistoryItem,
    OtherProcedureHistoryItem,
)
from manage_breast_screening.participants.models.symptom import (
    NippleChangeChoices,
    SkinChangeChoices,
)

from .. import models


class ParticipantAddressFactory(DjangoModelFactory):
    lines = ["123 Generic Street", "Townsville"]
    postcode = "SW1A 1AA"
    participant = None

    class Meta:
        model = models.ParticipantAddress
        django_get_or_create = ("participant", "lines", "postcode")


class ParticipantFactory(DjangoModelFactory):
    class Meta:
        model = models.Participant
        django_get_or_create = ("nhs_number",)
        skip_postgeneration_save = True

    first_name = Faker("first_name")
    last_name = Faker("last_name")
    gender = "Female"
    nhs_number = Sequence(lambda n: f"9{n:010d}")
    phone = "07700900829"
    email = "janet.williams@example.com"
    date_of_birth = date(1959, 7, 22)
    ethnic_background_id = FuzzyChoice(
        models.Participant.ETHNIC_BACKGROUND_CHOICES, getter=lambda c: c[0]
    )
    risk_level = "Routine"
    extra_needs = {}

    address = RelatedFactory(
        ParticipantAddressFactory, factory_related_name="participant"
    )


class ParticipantReportedMammogramFactory(DjangoModelFactory):
    class Meta:
        model = models.ParticipantReportedMammogram

    participant = SubFactory(ParticipantFactory)
    location_type = (
        models.ParticipantReportedMammogram.LocationType.NHS_BREAST_SCREENING_UNIT
    )
    provider = SubFactory(ProviderFactory)

    class Params:
        outside_uk = Trait(
            location_type=models.ParticipantReportedMammogram.LocationType.OUTSIDE_UK,
            location_details="france",
            provider=None,
        )
        elsewhere_uk = Trait(
            location_type=models.ParticipantReportedMammogram.LocationType.ELSEWHERE_UK,
            location_details="private provider",
            provider=None,
        )


class ScreeningEpisodeFactory(DjangoModelFactory):
    class Meta:
        model = models.ScreeningEpisode

    participant = SubFactory(ParticipantFactory)


class AppointmentStatusFactory(DjangoModelFactory):
    class Meta:
        model = models.AppointmentStatus

    appointment = None
    created_by = SubFactory(UserFactory)

    @post_generation
    def created_at(obj, create, extracted, **kwargs):
        if not create or not extracted:
            return

        obj.created_at = extracted
        obj.save()


class AppointmentFactory(DjangoModelFactory):
    class Meta:
        model = models.Appointment
        skip_postgeneration_save = True

    clinic_slot = SubFactory(ClinicSlotFactory)
    screening_episode = SubFactory(ScreeningEpisodeFactory)

    @post_generation
    def first_name(obj, create, extracted, **kwargs):
        if not create or not extracted:
            return

        obj.screening_episode.participant.first_name = extracted
        if create:
            obj.screening_episode.participant.save()

    @post_generation
    def last_name(obj, create, extracted, **kwargs):
        if not create or not extracted:
            return

        obj.screening_episode.participant.last_name = extracted
        if create:
            obj.screening_episode.participant.save()

    @post_generation
    def starts_at(obj, create, extracted, **kwargs):
        if not create or not extracted:
            return

        obj.clinic_slot.starts_at = extracted
        if create:
            obj.clinic_slot.save()

    # Allow passing an explicit status
    # e.g. `current_status=AppointmentStatus.CHECKED_IN`
    @post_generation
    def current_status(obj, create, extracted, **kwargs):
        if not create or not extracted:
            return

        obj.statuses.add(
            AppointmentStatusFactory.create(state=extracted, appointment=obj)
        )


class BreastCancerHistoryItemFactory(DjangoModelFactory):
    class Meta:
        model = models.BreastCancerHistoryItem

    appointment = SubFactory(AppointmentFactory)
    diagnosis_location = Iterator(BreastCancerHistoryItem.DiagnosisLocationChoices)
    left_breast_procedure = BreastCancerHistoryItem.Procedure.NO_PROCEDURE
    right_breast_procedure = BreastCancerHistoryItem.Procedure.NO_PROCEDURE
    left_breast_other_surgery = [BreastCancerHistoryItem.Surgery.NO_SURGERY]
    right_breast_other_surgery = [BreastCancerHistoryItem.Surgery.NO_SURGERY]
    left_breast_treatment = [BreastCancerHistoryItem.Treatment.NO_RADIOTHERAPY]
    right_breast_treatment = [BreastCancerHistoryItem.Treatment.NO_RADIOTHERAPY]


class MastectomyOrLumpectomyHistoryItemFactory(DjangoModelFactory):
    class Meta:
        model = models.MastectomyOrLumpectomyHistoryItem

    appointment = SubFactory(AppointmentFactory)
    right_breast_procedure = MastectomyOrLumpectomyHistoryItem.Procedure.NO_PROCEDURE
    left_breast_procedure = MastectomyOrLumpectomyHistoryItem.Procedure.NO_PROCEDURE
    right_breast_other_surgery = [MastectomyOrLumpectomyHistoryItem.Surgery.NO_SURGERY]
    left_breast_other_surgery = [MastectomyOrLumpectomyHistoryItem.Surgery.NO_SURGERY]
    year_of_surgery = None
    surgery_reason = MastectomyOrLumpectomyHistoryItem.SurgeryReason.OTHER_REASON
    additional_details = ""

    
class ImplantedMedicalDeviceHistoryItemFactory(DjangoModelFactory):
    class Meta:
        model = models.ImplantedMedicalDeviceHistoryItem

    appointment = SubFactory(AppointmentFactory)
    device = Iterator(ImplantedMedicalDeviceHistoryItem.Device)


class BreastAugmentationHistoryItemFactory(DjangoModelFactory):
    class Meta:
        model = models.BreastAugmentationHistoryItem

    appointment = SubFactory(AppointmentFactory)
    right_breast_procedures = [
        models.BreastAugmentationHistoryItem.Procedure.NO_PROCEDURES
    ]
    left_breast_procedures = [
        models.BreastAugmentationHistoryItem.Procedure.NO_PROCEDURES
    ]


class OtherProcedureHistoryItemFactory(DjangoModelFactory):
    class Meta:
        model = models.OtherProcedureHistoryItem

    appointment = SubFactory(AppointmentFactory)
    procedure = Iterator(OtherProcedureHistoryItem.Procedure)


class BenignLumpHistoryItemFactory(DjangoModelFactory):
    class Meta:
        model = models.BenignLumpHistoryItem

    appointment = SubFactory(AppointmentFactory)
    left_breast_procedures = [BenignLumpHistoryItem.Procedure.NO_PROCEDURES]
    right_breast_procedures = [BenignLumpHistoryItem.Procedure.NO_PROCEDURES]
    procedure_location = Iterator(BenignLumpHistoryItem.ProcedureLocation)


class SymptomFactory(DjangoModelFactory):
    class Meta:
        model = models.Symptom
        skip_postgeneration_save = True

    reported_at = LazyFunction(date.today)
    area = Iterator(models.SymptomAreas)
    intermittent = False
    investigated = False
    recently_resolved = False
    appointment = SubFactory(AppointmentFactory)
    area_description = LazyAttribute(
        lambda o: "" if o.area == models.SymptomAreas.BOTH_BREASTS else "abc"
    )

    class Params:
        lump = Trait(
            symptom_type_id=models.SymptomType.LUMP,
        )

        nipple_change = Trait(
            symptom_type_id=models.SymptomType.NIPPLE_CHANGE,
        )

        colour_change = Trait(
            symptom_type_id=models.SymptomType.SKIN_CHANGE,
            symptom_sub_type_id=SkinChangeChoices.COLOUR_CHANGE,
        )

        other_skin_change = Trait(
            symptom_type_id=models.SymptomType.SKIN_CHANGE,
            symptom_sub_type_id=SkinChangeChoices.OTHER,
        )

        swelling_or_shape_change = Trait(
            symptom_type_id=models.SymptomType.SWELLING_OR_SHAPE_CHANGE,
        )

        inversion = Trait(
            symptom_type_id=models.SymptomType.NIPPLE_CHANGE,
            symptom_sub_type_id=NippleChangeChoices.INVERSION,
        )

        other = Trait(
            symptom_type_id=models.SymptomType.OTHER, symptom_sub_type_details="abc"
        )
