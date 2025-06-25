import pytest
from pytest_django.asserts import assertQuerySetEqual

from manage_breast_screening.clinics.tests.factories import (
    ClinicFactory,
    ClinicSlotFactory,
)

from .. import models
from .factories import AppointmentFactory, ParticipantFactory, ScreeningEpisodeFactory


class TestParticipant:
    @pytest.mark.parametrize(
        "category,group",
        [
            ("White", "English, Welsh, Scottish, Northern Irish or British"),
            ("Asian or Asian British", "Pakistani"),
            (None, None),
        ],
    )
    def test_ethnic_group_category(self, category, group):
        assert (
            ParticipantFactory.build(ethnic_group=group).ethnic_group_category()
            == category
        )


@pytest.mark.django_db
class TestScreeningEvent:
    def test_no_previous_screening_episode(self):
        episode = ScreeningEpisodeFactory.create()
        assert episode.previous() is None

    def test_previous_screening_episode(self):
        episode = ScreeningEpisodeFactory.create()
        next_episode = ScreeningEpisodeFactory.create(participant=episode.participant)
        assert next_episode.previous() == episode


@pytest.mark.django_db
class TestAppointment:
    def test_appointment_filtering(self):
        confirmed = AppointmentFactory.create(
            current_status=models.AppointmentStatus.CONFIRMED
        )
        checked_in = AppointmentFactory.create(
            current_status=models.AppointmentStatus.CHECKED_IN
        )
        screened = AppointmentFactory.create(
            current_status=models.AppointmentStatus.SCREENED
        )
        cancelled = AppointmentFactory.create(
            current_status=models.AppointmentStatus.CANCELLED
        )
        did_not_attend = AppointmentFactory.create(
            current_status=models.AppointmentStatus.DID_NOT_ATTEND
        )
        partially_screened = AppointmentFactory.create(
            current_status=models.AppointmentStatus.PARTIALLY_SCREENED
        )
        attended_not_screened = AppointmentFactory.create(
            current_status=models.AppointmentStatus.ATTENDED_NOT_SCREENED
        )

        assertQuerySetEqual(
            models.Appointment.objects.remaining(),
            {confirmed, checked_in},
            ordered=False,
        )

        assertQuerySetEqual(
            models.Appointment.objects.checked_in(), {checked_in}, ordered=False
        )
        assertQuerySetEqual(
            models.Appointment.objects.complete(),
            {
                screened,
                cancelled,
                did_not_attend,
                partially_screened,
                attended_not_screened,
            },
            ordered=False,
        )

    def test_by_clinic_and_filter(self):
        # Create a clinic and clinic slots
        clinic = ClinicFactory.create()
        clinic_slot1 = ClinicSlotFactory.create(clinic=clinic)
        clinic_slot2 = ClinicSlotFactory.create(clinic=clinic)

        # Create another clinic to verify filtering works correctly
        other_clinic = ClinicFactory.create()
        other_slot = ClinicSlotFactory.create(clinic=other_clinic)

        # Create appointments with different statuses for our target clinic
        confirmed = AppointmentFactory.create(
            clinic_slot=clinic_slot1, current_status=models.AppointmentStatus.CONFIRMED
        )
        checked_in = AppointmentFactory.create(
            clinic_slot=clinic_slot2, current_status=models.AppointmentStatus.CHECKED_IN
        )
        screened = AppointmentFactory.create(
            clinic_slot=clinic_slot1, current_status=models.AppointmentStatus.SCREENED
        )

        # Create an appointment for the other clinic that should not appear in results
        AppointmentFactory.create(
            clinic_slot=other_slot, current_status=models.AppointmentStatus.CONFIRMED
        )

        assertQuerySetEqual(
            models.Appointment.objects.for_clinic_and_filter(clinic, "remaining"),
            {confirmed, checked_in},
            ordered=False,
        )
        assertQuerySetEqual(
            models.Appointment.objects.for_clinic_and_filter(clinic, "checked_in"),
            {checked_in},
            ordered=False,
        )
        assertQuerySetEqual(
            models.Appointment.objects.for_clinic_and_filter(clinic, "complete"),
            {screened},
            ordered=False,
        )
        assertQuerySetEqual(
            models.Appointment.objects.for_clinic_and_filter(clinic, "all"),
            {confirmed, checked_in, screened},
            ordered=False,
        )

    def test_filter_counts_for_clinic(self):
        # Create a clinic and clinic slots
        clinic = ClinicFactory.create()
        clinic_slot1 = ClinicSlotFactory.create(clinic=clinic)
        clinic_slot2 = ClinicSlotFactory.create(clinic=clinic)

        # Create appointments with different statuses
        AppointmentFactory.create(
            clinic_slot=clinic_slot1, current_status=models.AppointmentStatus.CONFIRMED
        )
        AppointmentFactory.create(
            clinic_slot=clinic_slot2, current_status=models.AppointmentStatus.CONFIRMED
        )
        AppointmentFactory.create(
            clinic_slot=clinic_slot1, current_status=models.AppointmentStatus.CHECKED_IN
        )
        AppointmentFactory.create(
            clinic_slot=clinic_slot2, current_status=models.AppointmentStatus.SCREENED
        )
        AppointmentFactory.create(
            clinic_slot=clinic_slot1, current_status=models.AppointmentStatus.CANCELLED
        )

        # Create another clinic with appointments that shouldn't be counted
        other_clinic = ClinicFactory.create()
        other_slot = ClinicSlotFactory.create(clinic=other_clinic)
        AppointmentFactory.create(
            clinic_slot=other_slot, current_status=models.AppointmentStatus.CONFIRMED
        )

        counts = models.Appointment.objects.filter_counts_for_clinic(clinic)

        assert counts["remaining"] == 3
        assert counts["checked_in"] == 1
        assert counts["complete"] == 2
        assert counts["all"] == 5


@pytest.mark.django_db
def test_appointment_current_status():
    appointment = AppointmentFactory.create(
        current_status=models.AppointmentStatus.CONFIRMED
    )
    appointment.statuses.create(state=models.AppointmentStatus.CHECKED_IN)

    assert appointment.statuses.first().state == models.AppointmentStatus.CHECKED_IN
    assert appointment.current_status.state == models.AppointmentStatus.CHECKED_IN
