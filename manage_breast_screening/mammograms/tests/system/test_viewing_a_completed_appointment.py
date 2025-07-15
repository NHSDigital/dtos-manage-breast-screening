import pytest
from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.core.system_test_setup import SystemTestCase
from manage_breast_screening.participants.models import AppointmentStatus
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)


class TestViewingACompletedAppointment(SystemTestCase):
    @pytest.fixture(autouse=True)
    def before(self):
        self.participant = ParticipantFactory(first_name="Janet", last_name="Williams")
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(
            screening_episode=self.screening_episode,
            current_status=AppointmentStatus.SCREENED,
        )

    def test_viewing_a_completed_appointment(self):
        """
        The appointment page includes appointment details, medical information, and images tabs.
        Only the first one is implemented yet.
        """
        self.given_i_am_on_the_appointment_show_page()
        self.then_i_should_see_the_demographic_banner()
        self.and_i_should_see_the_participant_details()
        self.and_i_should_not_see_a_form()

    def test_accessibility(self):
        self.given_i_am_on_the_appointment_show_page()
        self.then_the_accessibility_baseline_is_met()

    def given_i_am_on_the_appointment_show_page(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:show_appointment",
                kwargs={"pk": self.appointment.pk},
            )
        )

    def then_i_should_see_the_demographic_banner(self):
        expect(self.page.get_by_text("NHS Number")).to_be_visible()

    def and_i_should_see_the_participant_details(self):
        expect(
            self.page.locator(".nhsuk-summary-list__row", has_text="Full name")
        ).to_contain_text("Janet Williams")

    def and_i_should_not_see_a_form(self):
        expect(self.page.get_by_role("form")).not_to_be_attached()
