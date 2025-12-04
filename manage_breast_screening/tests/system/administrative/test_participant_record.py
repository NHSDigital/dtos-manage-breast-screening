import re
from datetime import datetime
from datetime import timezone as tz

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.clinics.tests.factories import ClinicSlotFactory
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)

from ..system_test_setup import SystemTestCase


class TestParticipantRecord(SystemTestCase):
    @pytest.fixture(autouse=True)
    def before(self, time_machine):
        self.participant = ParticipantFactory(first_name="Janet", last_name="Williams")

        time_machine.move_to(datetime(2025, 1, 1, 10, tzinfo=tz.utc))

    def test_viewing_participant_record_from_an_appointment(self):
        self.given_i_am_logged_in_as_an_administrative_user()
        self.and_the_participant_has_an_upcoming_appointment()
        self.and_i_am_viewing_the_upcoming_appointment()
        self.when_i_click_on_participant_details()
        self.then_i_should_be_on_the_participant_record_page()
        self.and_i_should_see_the_participant_record()
        self.when_i_click_on_the_back_link()
        self.then_i_should_be_back_on_the_appointment()

    def test_accessibility(self):
        self.given_i_am_logged_in_as_an_administrative_user()
        self.and_the_participant_has_an_upcoming_appointment()
        self.and_i_am_on_the_participant_details_tab()
        self.then_the_accessibility_baseline_is_met()

    def and_the_participant_has_an_upcoming_appointment(self):
        clinic_slot = ClinicSlotFactory(
            starts_at=datetime(2025, 1, 2, 11, tzinfo=tz.utc),
            clinic__setting__provider=self.current_provider,
        )
        screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.upcoming_appointment = AppointmentFactory(
            clinic_slot=clinic_slot,
            screening_episode=screening_episode,
        )

    def and_the_participant_has_past_appointments(self):
        clinic_slot_2022 = ClinicSlotFactory(
            starts_at=datetime(2022, 1, 2, 11, tzinfo=tz.utc),
            clinic__setting__provider=self.current_provider,
        )
        clinic_slot_2019 = ClinicSlotFactory(
            starts_at=datetime(2019, 1, 2, 11, tzinfo=tz.utc),
            clinic__setting__provider=self.current_provider,
        )
        self.past_appointments = [
            AppointmentFactory(
                clinic_slot=clinic_slot_2022,
                screening_episode=ScreeningEpisodeFactory(participant=self.participant),
            ),
            AppointmentFactory(
                clinic_slot=clinic_slot_2019,
                screening_episode=ScreeningEpisodeFactory(participant=self.participant),
            ),
        ]

    def and_i_am_viewing_the_upcoming_appointment(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:show_appointment",
                kwargs={"pk": self.upcoming_appointment.pk},
            )
        )

    def and_i_am_on_the_participant_details_tab(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:participant_details",
                kwargs={"pk": self.upcoming_appointment.pk},
            )
        )

    def when_i_click_on_participant_details(self):
        self.page.get_by_role("link", name="Participant details").click()

    def then_i_should_be_on_the_participant_record_page(self):
        path = reverse(
            "mammograms:participant_details",
            kwargs={"pk": self.upcoming_appointment.pk},
        )
        expect(self.page).to_have_url(re.compile(path))

    def and_i_should_see_the_participant_record(self):
        main = self.page.get_by_role("main")
        expect(main).to_contain_text("Janet Williams")
        expect(main).to_contain_text("Participant details")

    def when_i_click_on_the_back_link(self):
        self.page.get_by_role("link", name="Appointment details").click()

    def then_i_should_be_back_on_the_appointment(self):
        path = reverse(
            "mammograms:show_appointment",
            kwargs={"pk": self.upcoming_appointment.pk},
        )
        expect(self.page).to_have_url(re.compile(path))

    def then_i_should_see_the_upcoming_appointment(self):
        upcoming = self.page.get_by_test_id("upcoming-appointments-table")
        expect(upcoming).to_be_visible()
        appointment = upcoming.get_by_test_id("appointment-row")
        expect(appointment).to_be_visible()
        expect(appointment).to_contain_text("2 January 2025")

    def then_i_should_see_the_past_appointments(self):
        past = self.page.get_by_test_id("past-appointments-table")
        expect(past).to_be_visible()
        appointments = past.get_by_test_id("appointment-row").all()
        assert len(appointments) == 2

        expect(appointments[0]).to_contain_text("2 January 2022")
        expect(appointments[1]).to_contain_text("2 January 2019")

    def when_i_click_on_the_upcoming_appointment(self):
        past = self.page.get_by_test_id("upcoming-appointments-table")
        past.get_by_text("View details").click()

    def when_i_click_on_a_past_appointment(self):
        past = self.page.get_by_test_id("past-appointments-table")
        past.get_by_text("View details").first.click()

    def then_i_should_be_on_the_past_appointment_page(self):
        path = reverse(
            "mammograms:show_appointment",
            kwargs={"pk": self.past_appointments[0].pk},
        )
        expect(self.page).to_have_url(re.compile(path))

    def then_i_should_be_on_the_upcoming_appointment_page(self):
        path = reverse(
            "mammograms:show_appointment",
            kwargs={"pk": self.upcoming_appointment.pk},
        )
        expect(self.page).to_have_url(re.compile(path))
