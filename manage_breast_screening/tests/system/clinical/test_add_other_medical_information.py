from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)

from ..system_test_setup import SystemTestCase


class TestAddOtherMedicalInformation(SystemTestCase):
    def test_adding_other_medical_information(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()

        self.when_i_click_add_other_medical_information()
        self.then_i_see_the_add_other_medical_information_form()

        self.when_i_click_save()
        self.then_i_see_validation_error()

        self.when_i_enter_details("some info entered by user")
        self.and_i_click_save()
        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_message_says_other_medical_information_added()
        self.and_the_other_medical_information_is_displayed("some info entered by user")

        self.when_i_click_change_other_medical_information()
        self.then_i_see_the_edit_other_medical_information_form()

        self.when_i_enter_details("some updated info entered by user")
        self.and_i_click_save()
        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_message_says_other_medical_information_updated()
        self.and_the_other_medical_information_is_displayed(
            "some updated info entered by user"
        )

        self.when_i_mark_that_imaging_can_go_ahead()
        self.then_i_should_be_on_the_record_images_page()

        self.when_i_select_yes_2_cc_and_2_mlo()
        self.and_i_click_continue()
        self.then_i_should_be_on_the_check_information_page()
        self.and_the_medical_other_information_is_listed()

    def test_accessibility(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_add_other_medical_information_page()
        self.then_the_accessibility_baseline_is_met()

    def and_there_is_an_appointment(self):
        self.participant = ParticipantFactory(first_name="Angela", last_name="Jones")
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(
            screening_episode=self.screening_episode,
            clinic_slot__clinic__setting__provider=self.current_provider,
        )

    def and_i_am_on_the_record_medical_information_page(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": self.appointment.pk},
            )
        )

    def and_i_am_on_the_add_other_medical_information_page(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:add_other_medical_information",
                kwargs={"pk": self.appointment.pk},
            )
        )

    def when_i_click_add_other_medical_information(self):
        self.page.get_by_role(
            "link", name="Enter other medical information details"
        ).click()

    def when_i_click_change_other_medical_information(self):
        self.page.get_by_role("link", name="Change other medical information").click()

    def then_i_see_the_add_other_medical_information_form(self):
        expect(self.page.get_by_text("Other medical information")).to_be_visible()
        self.assert_page_title_contains("Add other medical information")

    def then_i_see_the_edit_other_medical_information_form(self):
        expect(self.page.get_by_text("Other medical information")).to_be_visible()
        self.assert_page_title_contains("Edit other medical information")

    def when_i_enter_details(self, details):
        self.page.get_by_label("Other medical information", exact=True).fill(details)

    def and_i_click_save(self):
        self.page.get_by_text("Save").click()

    when_i_click_save = and_i_click_save

    def then_i_see_validation_error(self):
        self.expect_validation_error(
            error_text="Provide details of any relevant health conditions or medications that are not covered by symptoms or medical history questions",
            field_label="Other medical information",
        )

    def then_i_am_back_on_the_medical_information_page(self):
        self.expect_url("mammograms:record_medical_information", pk=self.appointment.pk)

    def and_the_message_says_other_medical_information_added(self):
        alert = self.page.get_by_role("alert")

        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text("Added other medical information")

    def and_the_message_says_other_medical_information_updated(self):
        alert = self.page.get_by_role("alert")

        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text("Updated other medical information")

    def and_the_other_medical_information_is_displayed(self, expected_text):
        heading = self.page.get_by_role("heading").filter(has_text="Other information")
        section = self.page.locator(".nhsuk-card").filter(has=heading)
        expect(section).to_be_visible()

        row = section.locator(
            ".nhsuk-summary-list__row", has_text="Other medical information"
        )
        value = row.locator(".nhsuk-summary-list__value")
        expect(value).to_have_text(expected_text)

    def when_i_mark_that_imaging_can_go_ahead(self):
        buttons = self.page.get_by_role("button", name="Complete all and continue")
        assert buttons.count() == 2
        buttons.first.click()

    def then_i_should_be_on_the_record_images_page(self):
        self.expect_url("mammograms:take_images", pk=self.appointment.pk)
        self.assert_page_title_contains("Record images taken")

    def when_i_select_yes_2_cc_and_2_mlo(self):
        self.page.get_by_label("Yes, 2 CC and 2 MLO").click()

    def and_i_click_continue(self):
        self.page.get_by_text("Continue").click()

    def then_i_should_be_on_the_check_information_page(self):
        self.expect_url("mammograms:check_information", pk=self.appointment.pk)
        self.assert_page_title_contains("Check information")

    def and_the_medical_other_information_is_listed(self):
        heading = self.page.get_by_role("heading").filter(
            has_text="Medical Information"
        )
        section = self.page.locator(".nhsuk-card").filter(has=heading)
        expect(section).to_be_visible()

        row = section.locator(
            ".nhsuk-summary-list__row", has_text="Other relevant information"
        )
        value = row.locator(".nhsuk-summary-list__value")
        expect(value).to_contain_text("some updated info entered by user")
