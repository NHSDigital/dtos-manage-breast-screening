import re

from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.core.utils.string_formatting import format_nhs_number
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)

from ..system_test_setup import SystemTestCase


class TestMammogramWorkflow(SystemTestCase):
    def test_capturing_medical_information(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_appointment_show_page()

        self.when_i_click_start_this_appointment()
        self.then_i_should_be_on_the_confirm_identity_page()
        self.and_i_see_the_appointment_status_bar()

        self.when_i_click_confirm_identity()
        self.then_i_should_be_on_the_record_medical_information_page()
        self.and_i_see_the_appointment_status_bar()

        self.when_i_mark_that_imaging_can_go_ahead()
        self.then_the_screen_should_show_that_it_is_awaiting_images_from_the_PACS()

    def test_accessibility(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_appointment_show_page()

        self.when_i_click_start_this_appointment()
        self.then_the_accessibility_baseline_is_met()

        self.when_i_click_confirm_identity()
        self.then_the_accessibility_baseline_is_met()

        self.when_i_mark_that_imaging_can_go_ahead()
        self.then_the_accessibility_baseline_is_met()

    def and_there_is_an_appointment(self):
        self.participant = ParticipantFactory(first_name="Janet", last_name="Williams")
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(
            screening_episode=self.screening_episode,
            clinic_slot__clinic__setting__provider=self.current_provider,
        )

    def and_i_am_on_the_appointment_show_page(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:show_appointment",
                kwargs={"pk": self.appointment.pk},
            )
        )

    def then_i_should_see_the_demographic_banner(self):
        expect(self.page.get_by_text("NHS Number")).to_be_visible()

    def when_i_change_to_the_participant_details_tab(self):
        self.page.get_by_role("link", name="Participant details").click()

    def and_i_should_see_the_participant_details(self):
        expect(
            self.page.locator(".nhsuk-summary-list__row", has_text="Full name")
        ).to_contain_text("Janet Williams")

    then_i_should_see_the_participant_details = and_i_should_see_the_participant_details

    def when_i_click_start_this_appointment(
        self,
    ):
        self.page.get_by_text("Start this appointment").click()

    def when_i_submit_the_form(self):
        self.page.get_by_role("button", name="Continue").click()

    def then_i_should_be_on_the_confirm_identity_page(self):
        path = reverse(
            "mammograms:confirm_identity",
            kwargs={"pk": self.appointment.pk},
        )
        expect(self.page).to_have_url(re.compile(path))
        self.assert_page_title_contains("Confirm identity")

    def and_i_see_the_appointment_status_bar(self):
        status_bar = self.page.locator("div.app-status-bar")
        expect(status_bar).to_contain_text(
            format_nhs_number(self.participant.nhs_number)
        )
        expect(status_bar).to_contain_text(self.participant.full_name)

    def then_i_should_be_on_the_record_medical_information_page(self):
        path = reverse(
            "mammograms:record_medical_information",
            kwargs={"pk": self.appointment.pk},
        )
        expect(self.page).to_have_url(re.compile(path))
        self.assert_page_title_contains("Record medical information")

    def when_i_click_confirm_identity(self):
        self.page.get_by_role("button").filter(
            has_text="Confirm identity"
        ).first.click()

    def when_i_mark_that_imaging_can_go_ahead(self):
        button = self.page.get_by_role("button", name="Complete all and continue")
        button.click()

    def then_the_screen_should_show_that_it_is_awaiting_images_from_the_PACS(self):
        path = reverse(
            "mammograms:awaiting_images",
            kwargs={"pk": self.appointment.pk},
        )
        expect(self.page).to_have_url(re.compile(path))
        self.assert_page_title_contains("Awaiting images")
