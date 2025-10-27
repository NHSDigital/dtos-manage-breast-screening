import re

from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)

from ..system_test_setup import SystemTestCase


class TestRecordingAMammogram(SystemTestCase):
    def test_recording_a_mammogram_without_capturing_medical_information(self):
        """
        I can record a mammogram without entering any relevant medical information.
        """
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_appointment_show_page()
        self.then_i_should_see_the_demographic_banner()
        self.and_i_should_see_the_participant_details()

        self.when_i_click_start_this_appointment()
        self.then_i_should_be_on_the_medical_information_page()
        self.and_i_should_be_prompted_to_ask_about_relevant_medical_information()

        self.when_i_mark_that_the_participant_shared_no_medical_information()
        self.then_the_screen_should_show_that_it_is_awaiting_images_from_the_PACS()

    def test_capturing_medical_information(self):
        """
        I can optionally capture medical information as part of the mammogram appointment.
        """
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_appointment_show_page()

        self.when_i_click_start_this_appointment()
        self.then_i_should_be_on_the_medical_information_page()
        self.and_i_should_be_prompted_to_ask_about_relevant_medical_information()

        self.when_i_mark_that_the_participant_shared_medical_information()
        self.then_i_should_be_on_the_record_medical_information_page()
        self.when_i_mark_that_imaging_can_go_ahead()

        self.then_the_screen_should_show_that_it_is_awaiting_images_from_the_PACS()

    def test_filling_out_forms_incorrectly(self):
        """
        At each step in the flow, when I fill out the forms incorrectly,
        then I should see the errors so I can fix them.
        """
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_appointment_show_page()

        self.when_i_click_start_this_appointment()
        self.then_i_should_be_on_the_medical_information_page()

        self.when_i_submit_the_form()
        self.then_i_am_prompted_to_answer_has_the_participant_shared_medical_info()

        self.when_i_mark_that_the_participant_shared_medical_information()
        self.then_i_should_be_on_the_record_medical_information_page()

        self.when_i_submit_the_form()
        self.then_i_am_prompted_to_confirm_whether_imaging_can_go_ahead()

    def test_accessibility(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_appointment_show_page()
        self.then_the_accessibility_baseline_is_met()

        self.when_i_click_start_this_appointment()
        self.then_the_accessibility_baseline_is_met()

        self.when_i_mark_that_the_participant_shared_medical_information()
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

    def and_i_should_see_the_participant_details(self):
        expect(
            self.page.locator(".nhsuk-summary-list__row", has_text="Full name")
        ).to_contain_text("Janet Williams")

    def when_i_click_start_this_appointment(
        self,
    ):
        self.page.get_by_text("Start this appointment").click()

    def when_i_submit_the_form(self):
        self.page.get_by_role("button", name="Continue").click()

    def then_i_should_be_on_the_medical_information_page(self):
        path = reverse(
            "mammograms:ask_for_medical_information",
            kwargs={"pk": self.appointment.pk},
        )
        expect(self.page).to_have_url(re.compile(path))
        self.assert_page_title_contains("Medical information")

    def then_i_should_be_on_the_record_medical_information_page(self):
        path = reverse(
            "mammograms:record_medical_information",
            kwargs={"pk": self.appointment.pk},
        )
        expect(self.page).to_have_url(re.compile(path))
        self.assert_page_title_contains("Record medical information")

    def and_i_should_be_prompted_to_ask_about_relevant_medical_information(self):
        expect(
            self.page.get_by_text(
                "Has the participant shared any relevant medical information?"
            )
        ).to_be_visible()

    def when_i_mark_that_the_participant_shared_no_medical_information(self):
        self.page.get_by_label("No - proceed to imaging").check()
        self.page.get_by_role("button", name="Continue").click()

    def when_i_mark_that_the_participant_shared_medical_information(self):
        self.page.get_by_label("Yes").check()
        self.page.get_by_role("button", name="Continue").click()

    def when_i_mark_that_imaging_can_go_ahead(self):
        self.page.get_by_label(
            "Yes, mark incomplete sections as ‘none’ or ‘no’"
        ).check()
        self.page.get_by_role("button", name="Continue").click()

    def then_the_screen_should_show_that_it_is_awaiting_images_from_the_PACS(self):
        path = reverse(
            "mammograms:awaiting_images",
            kwargs={"pk": self.appointment.pk},
        )
        expect(self.page).to_have_url(re.compile(path))
        self.assert_page_title_contains("Awaiting images")

    def then_i_am_prompted_to_answer_can_the_screening_go_ahead(self):
        self.expect_validation_error(
            error_text="This field is required.",
            fieldset_legend="Can the appointment go ahead?",
            field_label="Yes, go to medical information",
        )

    def then_i_am_prompted_to_answer_has_the_participant_shared_medical_info(self):
        self.expect_validation_error(
            error_text="This field is required.",
            fieldset_legend="Has the participant shared any relevant medical information?",
            field_label="Yes",
        )

    def then_i_am_prompted_to_confirm_whether_imaging_can_go_ahead(self):
        self.expect_validation_error(
            error_text="This field is required.",
            fieldset_legend="Can imaging go ahead?",
            field_label="Yes, mark incomplete sections as ‘none’ or ‘no’",
        )
