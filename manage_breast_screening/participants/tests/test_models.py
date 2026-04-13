from datetime import datetime
from datetime import timezone as tz

import pytest
from pytest_django.asserts import assertQuerySetEqual

from manage_breast_screening.clinics.tests.factories import (
    ClinicFactory,
    ClinicSlotFactory,
)
from manage_breast_screening.participants.models.appointment import (
    Appointment,
    AppointmentStatusNames,
)
from manage_breast_screening.participants.models.medical_history.implanted_medical_device_history_item import (
    ImplantedMedicalDeviceHistoryItem,
)

from .. import models
from .factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)


@pytest.mark.django_db
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
                "any_other_ethnic_background",
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

    def test_last_confirmed_mammogram_none(self):
        participant = ParticipantFactory.create()
        assert participant.last_confirmed_mammogram is None

    def test_last_confirmed_mammogram_one(self):
        participant = ParticipantFactory.create()

        mammogram = participant.confirmed_previous_mammograms.create(
            exact_date=datetime(2020, 1, 1, tzinfo=tz.utc)
        )

        assert participant.last_confirmed_mammogram == mammogram

    def test_last_confirmed_mammogram(self):
        participant = ParticipantFactory.create()
        assert participant.last_confirmed_mammogram is None

        participant.confirmed_previous_mammograms.create(
            exact_date=datetime(2020, 1, 1, tzinfo=tz.utc)
        )
        participant.confirmed_previous_mammograms.create(
            exact_date=datetime(2022, 12, 31, tzinfo=tz.utc)
        )
        last_confirmed_mammogram = participant.confirmed_previous_mammograms.create(
            exact_date=datetime(2023, 1, 1, tzinfo=tz.utc)
        )
        participant.confirmed_previous_mammograms.create(
            exact_date=datetime(2021, 1, 1, tzinfo=tz.utc)
        )

        assert participant.last_confirmed_mammogram == last_confirmed_mammogram


@pytest.mark.django_db
class TestScreeningEpisode:
    def test_no_previous_screening_episode(self):
        episode = ScreeningEpisodeFactory.create()
        assert episode.previous() is None

    def test_previous_screening_episode(self):
        episode = ScreeningEpisodeFactory.create()
        next_episode = ScreeningEpisodeFactory.create(participant=episode.participant)
        assert next_episode.previous() == episode


@pytest.mark.django_db
class TestAppointment:
    def test_status_filtering(self):
        confirmed = AppointmentFactory.create(status=AppointmentStatusNames.SCHEDULED)
        checked_in = AppointmentFactory.create(status=AppointmentStatusNames.CHECKED_IN)
        screened = AppointmentFactory.create(status=AppointmentStatusNames.SCREENED)
        cancelled = AppointmentFactory.create(status=AppointmentStatusNames.CANCELLED)
        did_not_attend = AppointmentFactory.create(
            status=AppointmentStatusNames.DID_NOT_ATTEND
        )
        partially_screened = AppointmentFactory.create(
            status=AppointmentStatusNames.PARTIALLY_SCREENED
        )
        attended_not_screened = AppointmentFactory.create(
            status=AppointmentStatusNames.ATTENDED_NOT_SCREENED
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
        confirmed = AppointmentFactory.create(status=AppointmentStatusNames.SCHEDULED)
        checked_in = AppointmentFactory.create(status=AppointmentStatusNames.CHECKED_IN)
        in_progress = AppointmentFactory.create(
            status=AppointmentStatusNames.IN_PROGRESS
        )
        paused = AppointmentFactory.create(status=AppointmentStatusNames.PAUSED)
        screened = AppointmentFactory.create(status=AppointmentStatusNames.SCREENED)

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
            models.Appointment.objects.for_filter("in_progress"),
            {in_progress, paused},
            ordered=False,
        )
        assertQuerySetEqual(
            models.Appointment.objects.for_filter("complete"),
            {screened},
            ordered=False,
        )
        assertQuerySetEqual(
            models.Appointment.objects.for_filter("all"),
            {confirmed, checked_in, in_progress, paused, screened},
            ordered=False,
        )

    def test_filter_counts_for_clinic(self):
        # Create a clinic and clinic slots
        clinic = ClinicFactory.create()
        clinic_slot1 = ClinicSlotFactory.create(clinic=clinic)
        clinic_slot2 = ClinicSlotFactory.create(clinic=clinic)

        # Create appointments with different statuses
        AppointmentFactory.create(
            clinic_slot=clinic_slot1, status=AppointmentStatusNames.SCHEDULED
        )
        AppointmentFactory.create(
            clinic_slot=clinic_slot2, status=AppointmentStatusNames.SCHEDULED
        )
        AppointmentFactory.create(
            clinic_slot=clinic_slot1, status=AppointmentStatusNames.CHECKED_IN
        )
        AppointmentFactory.create(
            clinic_slot=clinic_slot2, status=AppointmentStatusNames.SCREENED
        )
        AppointmentFactory.create(
            clinic_slot=clinic_slot1, status=AppointmentStatusNames.CANCELLED
        )

        # Create another clinic with appointments that shouldn't be counted
        other_clinic = ClinicFactory.create()
        other_slot = ClinicSlotFactory.create(clinic=other_clinic)
        AppointmentFactory.create(
            clinic_slot=other_slot, status=AppointmentStatusNames.SCHEDULED
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

    def test_for_participant(self):
        a = AppointmentFactory.create()
        b = AppointmentFactory.create(
            screening_episode__participant=a.screening_episode.participant
        )
        AppointmentFactory.create()

        assertQuerySetEqual(
            models.Appointment.objects.for_participant(
                a.screening_episode.participant_id
            ),
            [a, b],
            ordered=False,
        )


@pytest.mark.django_db
class TestCurrentStatus:
    def test_returns_current_status(self, django_assert_num_queries):
        latest_status = AppointmentStatusNames.IN_PROGRESS
        AppointmentFactory.create(status=latest_status)

        fetched_appointment = models.Appointment.objects.first()
        assert fetched_appointment.current_status.name == latest_status

    def test_returns_default_status_if_no_statuses(self, django_assert_num_queries):
        appointment = AppointmentFactory.create()
        assert appointment.current_status.name == AppointmentStatusNames.SCHEDULED


class TestAppointmentStatus:
    class TestActive:
        def test_active_statuses_return_true(self):
            assert Appointment(status=AppointmentStatusNames.SCHEDULED).active
            assert Appointment(status=AppointmentStatusNames.CHECKED_IN).active
            assert Appointment(status=AppointmentStatusNames.IN_PROGRESS).active
            assert not Appointment(status=AppointmentStatusNames.CANCELLED).active
            assert not Appointment(status=AppointmentStatusNames.DID_NOT_ATTEND).active
            assert not Appointment(
                status=AppointmentStatusNames.ATTENDED_NOT_SCREENED
            ).active
            assert not Appointment(
                status=AppointmentStatusNames.PARTIALLY_SCREENED
            ).active
            assert not Appointment(status=AppointmentStatusNames.SCREENED).active


class TestImplantedMedicalDeviceHistoryItem:
    @pytest.mark.parametrize(
        "name,lower,expected",
        [
            ("CARDIAC_DEVICE", False, "Cardiac device"),
            ("CARDIAC_DEVICE", True, "cardiac device"),
            ("HICKMAN_LINE", False, "Hickman line"),
            ("HICKMAN_LINE", True, "Hickman line"),
            ("OTHER_MEDICAL_DEVICE", False, "Other medical device"),
            ("OTHER_MEDICAL_DEVICE", True, "other medical device"),
            (
                ImplantedMedicalDeviceHistoryItem.Device.CARDIAC_DEVICE,
                False,
                "Cardiac device",
            ),
            (
                ImplantedMedicalDeviceHistoryItem.Device.CARDIAC_DEVICE,
                True,
                "cardiac device",
            ),
            (
                ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                False,
                "Hickman line",
            ),
            (
                ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                True,
                "Hickman line",
            ),
            (
                ImplantedMedicalDeviceHistoryItem.Device.OTHER_MEDICAL_DEVICE,
                False,
                "Other medical device",
            ),
            (
                ImplantedMedicalDeviceHistoryItem.Device.OTHER_MEDICAL_DEVICE,
                True,
                "other medical device",
            ),
        ],
    )
    def test_short_name(self, name, lower, expected):
        assert expected == ImplantedMedicalDeviceHistoryItem.Device.short_name(
            name, lower=lower
        )
