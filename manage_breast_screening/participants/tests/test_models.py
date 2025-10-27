from datetime import datetime
from datetime import timezone as tz
from random import choice

import pytest
from pytest_django.asserts import assertQuerySetEqual

from manage_breast_screening.clinics.tests.factories import (
    ClinicFactory,
    ClinicSlotFactory,
)

from .. import models
from ..models import AppointmentStatus, Ethnicity
from .factories import AppointmentFactory, ParticipantFactory, ScreeningEpisodeFactory


class TestParticipant:
    @pytest.mark.parametrize(
        "category,background_id",
        [
            ("White", "english_welsh_scottish_ni_british"),
            ("Asian or Asian British", "pakistani"),
        ],
    )
    def test_ethnic_category(self, category, background_id):
        assert (
            ParticipantFactory.build(ethnic_background_id=background_id).ethnic_category
            == category
        )

    @pytest.mark.parametrize(
        "background_id,any_other_background_details,display_name",
        [
            ("", None, None),
            ("invalid_id", None, None),
            (
                "english_welsh_scottish_ni_british",
                None,
                "English, Welsh, Scottish, Northern Irish or British",
            ),
            ("pakistani", "custom ethnicity", "Pakistani"),
            ("any_other_white_background", None, "Any other White background"),
            (
                choice(Ethnicity.non_specific_ethnic_backgrounds()),
                "custom ethnicity",
                "custom ethnicity",
            ),
        ],
    )
    def test_ethnic_background(
        self, background_id, any_other_background_details, display_name
    ):
        assert (
            ParticipantFactory.build(
                ethnic_background_id=background_id,
                any_other_background_details=any_other_background_details,
            ).ethnic_background
            == display_name
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
    def test_state_filtering(self):
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

    def test_upcoming_past_filters(self, time_machine):
        time_machine.move_to(datetime(2025, 1, 1, 10, tzinfo=tz.utc))

        # > 00:00 so counts as upcoming still
        earlier_today = AppointmentFactory.create(
            starts_at=datetime(2025, 1, 1, 9, tzinfo=tz.utc)
        )

        # past
        yesterday = AppointmentFactory.create(
            starts_at=datetime(2024, 12, 31, 9, tzinfo=tz.utc)
        )

        # upcoming
        tomorrow = AppointmentFactory.create(
            starts_at=datetime(2025, 1, 2, 9, tzinfo=tz.utc)
        )

        assertQuerySetEqual(
            models.Appointment.objects.past(), [yesterday], ordered=False
        )
        assertQuerySetEqual(
            models.Appointment.objects.upcoming(),
            [earlier_today, tomorrow],
            ordered=False,
        )

    def test_for_filter(self):
        confirmed = AppointmentFactory.create(
            current_status=models.AppointmentStatus.CONFIRMED
        )
        checked_in = AppointmentFactory.create(
            current_status=models.AppointmentStatus.CHECKED_IN
        )
        screened = AppointmentFactory.create(
            current_status=models.AppointmentStatus.SCREENED
        )

        assertQuerySetEqual(
            models.Appointment.objects.for_filter("remaining"),
            {confirmed, checked_in},
            ordered=False,
        )
        assertQuerySetEqual(
            models.Appointment.objects.for_filter("checked_in"),
            {checked_in},
            ordered=False,
        )
        assertQuerySetEqual(
            models.Appointment.objects.for_filter("complete"),
            {screened},
            ordered=False,
        )
        assertQuerySetEqual(
            models.Appointment.objects.for_filter("all"),
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

        counts = models.Appointment.filter_counts_for_clinic(clinic)

        assert counts["remaining"] == 3
        assert counts["checked_in"] == 1
        assert counts["complete"] == 2
        assert counts["all"] == 5

    def test_order_by_starts_at(self):
        early = AppointmentFactory.create(
            starts_at=datetime(2025, 1, 1, 9, tzinfo=tz.utc)
        )
        middle = AppointmentFactory.create(
            starts_at=datetime(2025, 1, 2, 10, tzinfo=tz.utc)
        )
        late = AppointmentFactory.create(
            starts_at=datetime(2025, 1, 3, 14, tzinfo=tz.utc)
        )

        assertQuerySetEqual(
            models.Appointment.objects.order_by_starts_at(),
            [early, middle, late],
        )

        assertQuerySetEqual(
            models.Appointment.objects.order_by_starts_at(desc=True),
            [late, middle, early],
        )


@pytest.mark.django_db
def test_appointment_current_status():
    appointment = AppointmentFactory.create(
        current_status=models.AppointmentStatus.CONFIRMED
    )
    appointment.statuses.create(state=models.AppointmentStatus.CHECKED_IN)

    assert appointment.statuses.first().state == models.AppointmentStatus.CHECKED_IN
    assert appointment.current_status.state == models.AppointmentStatus.CHECKED_IN


def test_appointment_status_active():
    assert AppointmentStatus(state=AppointmentStatus.CONFIRMED).active
    assert AppointmentStatus(state=AppointmentStatus.CHECKED_IN).active
    assert not AppointmentStatus(state=AppointmentStatus.CANCELLED).active
    assert not AppointmentStatus(state=AppointmentStatus.DID_NOT_ATTEND).active
    assert not AppointmentStatus(state=AppointmentStatus.ATTENDED_NOT_SCREENED).active
    assert not AppointmentStatus(state=AppointmentStatus.PARTIALLY_SCREENED).active
    assert not AppointmentStatus(state=AppointmentStatus.SCREENED).active
