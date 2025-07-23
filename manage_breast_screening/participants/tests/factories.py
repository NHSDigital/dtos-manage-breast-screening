from datetime import date

from factory import post_generation
from factory.declarations import SubFactory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice

from manage_breast_screening.clinics.tests.factories import ClinicSlotFactory

from .. import models


class ParticipantFactory(DjangoModelFactory):
    class Meta:
        model = models.Participant

    first_name = "Janet"
    last_name = "Williams"
    gender = "Female"
    nhs_number = "07700900829"
    phone = "07700900829"
    email = "janet.williams@example.com"
    date_of_birth = date(1959, 7, 22)
    ethnic_background_id = FuzzyChoice(
        models.Participant.ETHNIC_BACKGROUND_CHOICES, getter=lambda c: c[0]
    )
    risk_level = "Routine"
    extra_needs = {}


class ParticipantAddressFactory(DjangoModelFactory):
    lines = ["123 Generic Street", "Townsville"]
    postcode = "SW1A 1AA"
    participant = SubFactory(ParticipantFactory)

    class Meta:
        model = models.ParticipantAddress


class ScreeningEpisodeFactory(DjangoModelFactory):
    class Meta:
        model = models.ScreeningEpisode

    participant = SubFactory(ParticipantFactory)


class AppointmentStatusFactory(DjangoModelFactory):
    class Meta:
        model = models.AppointmentStatus

    appointment = None


class AppointmentFactory(DjangoModelFactory):
    class Meta:
        model = models.Appointment
        skip_postgeneration_save = True

    clinic_slot = SubFactory(ClinicSlotFactory)
    screening_episode = SubFactory(ScreeningEpisodeFactory)

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
