from datetime import datetime
from datetime import timezone as tz
from random import choice

import pytest
from pytest_django.asserts import assertQuerySetEqual

from manage_breast_screening.clinics.tests.factories import (
    ClinicFactory,
    ClinicSlotFactory,
)
from manage_breast_screening.participants.models.appointment import (
    AppointmentStatusNames,
)
from manage_breast_screening.participants.models.medical_history.implanted_medical_device_history_item import (
    ImplantedMedicalDeviceHistoryItem,
)

from .. import models
from ..models import AppointmentStatus, Ethnicity
from .factories import (
    AppointmentFactory,
    AppointmentStatusFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)


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
    def test_status_filtering(self):
        confirmed = AppointmentFactory.create(
            current_status=AppointmentStatusNames.SCHEDULED
        )
        checked_in = AppointmentFactory.create(
            current_status=AppointmentStatusNames.CHECKED_IN
        )
        screened = AppointmentFactory.create(
            current_status=AppointmentStatusNames.SCREENED
        )
        cancelled = AppointmentFactory.create(
            current_status=AppointmentStatusNames.CANCELLED
        )
        did_not_attend = AppointmentFactory.create(
            current_status=AppointmentStatusNames.DID_NOT_ATTEND
        )
        partially_screened = AppointmentFactory.create(
            current_status=AppointmentStatusNames.PARTIALLY_SCREENED
        )
        attended_not_screened = AppointmentFactory.create(
            current_status=AppointmentStatusNames.ATTENDED_NOT_SCREENED
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
            current_status=AppointmentStatusNames.SCHEDULED
        )
        checked_in = AppointmentFactory.create(
            current_status=AppointmentStatusNames.CHECKED_IN
        )
        in_progress = AppointmentFactory.create(
            current_status=AppointmentStatusNames.IN_PROGRESS
        )
        paused = AppointmentFactory.create(current_status=AppointmentStatusNames.PAUSED)
        screened = AppointmentFactory.create(
            current_status=AppointmentStatusNames.SCREENED
        )

        assertQuerySetEqual(
            models.Appointment.objects.for_filter("remaining"),
            {confirmed, checked_in, in_progress, paused},
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
            clinic_slot=clinic_slot1, current_status=AppointmentStatusNames.SCHEDULED
        )
        AppointmentFactory.create(
            clinic_slot=clinic_slot2, current_status=AppointmentStatusNames.SCHEDULED
        )
        AppointmentFactory.create(
            clinic_slot=clinic_slot1, current_status=AppointmentStatusNames.CHECKED_IN
        )
        AppointmentFactory.create(
            clinic_slot=clinic_slot2, current_status=AppointmentStatusNames.SCREENED
        )
        AppointmentFactory.create(
            clinic_slot=clinic_slot1, current_status=AppointmentStatusNames.CANCELLED
        )

        # Create another clinic with appointments that shouldn't be counted
        other_clinic = ClinicFactory.create()
        other_slot = ClinicSlotFactory.create(clinic=other_clinic)
        AppointmentFactory.create(
            clinic_slot=other_slot, current_status=AppointmentStatusNames.SCHEDULED
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

    def test_in_status_only_matches_latest_status_not_history(
        self, django_assert_num_queries
    ):
        appointment = AppointmentFactory.create()
        appointment_with_history = AppointmentFactory.create()

        AppointmentStatusFactory.create(
            appointment=appointment,
            name=AppointmentStatusNames.CHECKED_IN,
            created_at=datetime(2025, 1, 1, 9, tzinfo=tz.utc),
        )
        AppointmentStatusFactory.create(
            appointment=appointment_with_history,
            name=AppointmentStatusNames.CHECKED_IN,
            created_at=datetime(2025, 1, 2, 10, tzinfo=tz.utc),
        )
        AppointmentStatusFactory.create(
            appointment=appointment_with_history,
            name=AppointmentStatusNames.SCREENED,
            created_at=datetime(2025, 1, 2, 11, tzinfo=tz.utc),
        )

        with django_assert_num_queries(3):
            assertQuerySetEqual(
                models.Appointment.objects.in_status(AppointmentStatusNames.CHECKED_IN),
                [appointment],
                ordered=False,
            )
            assertQuerySetEqual(
                models.Appointment.objects.in_status(
                    AppointmentStatusNames.CHECKED_IN,
                    AppointmentStatusNames.SCREENED,
                ),
                [appointment, appointment_with_history],
                ordered=False,
            )
            assertQuerySetEqual(
                models.Appointment.objects.in_status(AppointmentStatusNames.SCREENED),
                [appointment_with_history],
                ordered=False,
            )

    @pytest.mark.django_db
    class TestEagerLoadCurrentStatus:
        def test_eager_loads_most_recent_status_with_created_by(
            self, django_assert_num_queries
        ):
            appointment = AppointmentFactory.create()

            latest_status = AppointmentStatusFactory.create(
                appointment=appointment,
                name=AppointmentStatusNames.IN_PROGRESS,
                created_at=datetime(2025, 1, 1, 10, tzinfo=tz.utc),
            )

            AppointmentStatusFactory.create(
                appointment=appointment,
                name=AppointmentStatusNames.CHECKED_IN,
                created_at=datetime(2025, 1, 1, 9, tzinfo=tz.utc),
            )

            AppointmentStatusFactory.create(
                appointment=appointment,
                name=AppointmentStatusNames.SCHEDULED,
                created_at=datetime(2025, 1, 1, 8, tzinfo=tz.utc),
            )

            appointment_with_status = (
                models.Appointment.objects.prefetch_current_status().get(
                    pk=appointment.pk
                )
            )

            prefetched_status = appointment_with_status._prefetched_current_status[0]
            assert prefetched_status == latest_status
            # Verify no additional queries when accessing created_by
            with django_assert_num_queries(0):
                assert prefetched_status.created_by is not None
                prefetched_status.created_by.nhs_uid

    @pytest.mark.django_db
    class TestCurrentStatus:
        def test_returns_prefetched_current_status_if_available(
            self, django_assert_num_queries
        ):
            appointment = AppointmentFactory.create()
            latest_status = AppointmentStatusFactory.create(
                appointment=appointment,
                name=AppointmentStatusNames.IN_PROGRESS,
                created_at=datetime(2025, 1, 1, 9, tzinfo=tz.utc),
            )
            AppointmentStatusFactory.create(
                appointment=appointment,
                name=AppointmentStatusNames.CHECKED_IN,
                created_at=datetime(2025, 1, 1, 8, tzinfo=tz.utc),
            )

            fetched_appointment = (
                models.Appointment.objects.prefetch_current_status().first()
            )
            with django_assert_num_queries(0):
                fetched_appointment.current_status.created_by
            assert fetched_appointment.current_status == latest_status

        def test_returns_current_status_even_if_not_prefetched(
            self, django_assert_num_queries
        ):
            appointment = AppointmentFactory.create()
            latest_status = AppointmentStatusFactory.create(
                appointment=appointment,
                name=AppointmentStatusNames.IN_PROGRESS,
                created_at=datetime(2025, 1, 1, 9, tzinfo=tz.utc),
            )
            AppointmentStatusFactory.create(
                appointment=appointment,
                name=AppointmentStatusNames.CHECKED_IN,
                created_at=datetime(2025, 1, 1, 8, tzinfo=tz.utc),
            )

            fetched_appointment = models.Appointment.objects.first()
            with django_assert_num_queries(2):
                fetched_appointment.current_status.created_by
            assert fetched_appointment.current_status == latest_status

        def test_returns_default_status_if_no_statuses(self, django_assert_num_queries):
            appointment = AppointmentFactory.create()
            assert appointment.current_status.name == AppointmentStatusNames.SCHEDULED


class TestAppointmentStatus:
    class TestActive:
        def test_active_statuses_return_true(self):
            assert AppointmentStatus(name=AppointmentStatusNames.SCHEDULED).active
            assert AppointmentStatus(name=AppointmentStatusNames.CHECKED_IN).active
            assert AppointmentStatus(name=AppointmentStatusNames.IN_PROGRESS).active
            assert not AppointmentStatus(name=AppointmentStatusNames.CANCELLED).active
            assert not AppointmentStatus(
                name=AppointmentStatusNames.DID_NOT_ATTEND
            ).active
            assert not AppointmentStatus(
                name=AppointmentStatusNames.ATTENDED_NOT_SCREENED
            ).active
            assert not AppointmentStatus(
                name=AppointmentStatusNames.PARTIALLY_SCREENED
            ).active
            assert not AppointmentStatus(name=AppointmentStatusNames.SCREENED).active


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
