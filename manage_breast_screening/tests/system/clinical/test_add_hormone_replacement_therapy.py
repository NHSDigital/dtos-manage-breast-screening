import allure
from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)

from ..system_test_setup import SystemTestCase


@allure.epic("Mammogram appointment")
@allure.feature("Add hormone replacement therapy to medical history")
class TestAddHormoneReplacementTherapy(SystemTestCase):
    def test_adding_hormone_replacement_therapy(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()

        self.when_i_click_add_hormone_replacement_therapy()
        self.then_i_see_the_add_hormone_replacement_therapy_form()

        self.when_i_click_continue()
        self.then_i_see_validation_error_for_missing_status()

        self.when_i_select_no()
        self.and_i_click_continue()

        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_message_says_hormone_replacement_therapy_added()
        self.and_the_hormone_replacement_therapy_is_displayed_as_not_taken()

        self.when_i_click_change_hormone_replacement_therapy()
        self.then_i_see_the_edit_hormone_replacement_therapy_form()

        self.when_i_select_yes()
        self.and_enter_a_duration()
        self.and_i_click_continue()

        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_message_says_hormone_replacement_therapy_updated()
        self.and_the_hormone_replacement_therapy_is_displayed_as_taken()

    def test_accessibility(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_add_hormone_replacement_therapy_page()
        self.then_the_accessibility_baseline_is_met()

    @allure.step("And there is an appointment")
    def and_there_is_an_appointment(self):
        self.participant = ParticipantFactory(first_name="Angela", last_name="Jones")
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(
            screening_episode=self.screening_episode,
            clinic_slot__clinic__setting__provider=self.current_provider,
        )

    @allure.step("And I am on the Record Medical Information page")
    def and_i_am_on_the_record_medical_information_page(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": self.appointment.pk},
            )
        )

    @allure.step("And I am on the Add Hormone Replacement Therapy page")
    def and_i_am_on_the_add_hormone_replacement_therapy_page(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:add_hormone_replacement_therapy",
                kwargs={"pk": self.appointment.pk},
            )
        )

    @allure.step("When I click 'Add Hormone Replacment Therapy'")
    def when_i_click_add_hormone_replacement_therapy(self):
        self.page.get_by_role(
            "link", name="Enter hormone replacement therapy (HRT) details"
        ).click()

    @allure.step("When I click 'Change'")
    def when_i_click_change_hormone_replacement_therapy(self):
        self.page.get_by_role("link", name="Change hormone replacement therapy").click()

    @allure.step("Then I see the Add Hormone Replacement Therapy form'")
    def then_i_see_the_add_hormone_replacement_therapy_form(self):
        expect(
            self.page.get_by_text("Is Angela Jones currently taking HRT?")
        ).to_be_visible()
        self.assert_page_title_contains("Add hormone replacement therapy")

    @allure.step("Then I see the Edit Hormone Replacement Therarpy form")
    def then_i_see_the_edit_hormone_replacement_therapy_form(self):
        expect(
            self.page.get_by_text("Is Angela Jones currently taking HRT?")
        ).to_be_visible()
        self.assert_page_title_contains("Edit hormone replacement therapy")

    @allure.step("When I select 'No'")
    def when_i_select_no(self):
        self.page.get_by_label("No", exact=True).click()

    @allure.step("When I select 'Yes'")
    def when_i_select_yes(self):
        self.page.get_by_label("Yes", exact=True).click()

    @allure.step("And enter a duration")
    def and_enter_a_duration(self):
        self.page.get_by_label("Approximate date started", exact=True).fill(
            "August 2024"
        )

    @allure.step("And I click continue")
    def and_i_click_continue(self):
        self.page.get_by_text("Continue").click()

    @allure.step("When I click continue")
    def when_i_click_continue(self):
        self.page.get_by_text("Continue").click()

    @allure.step("Then I see a validation error for the missing status")
    def then_i_see_validation_error_for_missing_status(self):
        self.expect_validation_error(
            error_text="Select whether they are currently taking HRT or not",
            fieldset_legend="Is Angela Jones currently taking HRT?",
            field_label="Yes",
        )

    @allure.step("Then I am back on the Record Medical Information page")
    def then_i_am_back_on_the_medical_information_page(self):
        self.expect_url("mammograms:record_medical_information", pk=self.appointment.pk)

    @allure.step("And the message says 'Added hormone replacement therapy'")
    def and_the_message_says_hormone_replacement_therapy_added(self):
        alert = self.page.get_by_role("alert")

        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text("Added hormone replacement therapy")

    @allure.step("And the message says 'Updated hormone replacement therapy'")
    def and_the_message_says_hormone_replacement_therapy_updated(self):
        alert = self.page.get_by_role("alert")

        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text("Updated hormone replacement therapy")

    @allure.step("And the hormone replacement therapy is displayed as 'Not taking HRT'")
    def and_the_hormone_replacement_therapy_is_displayed_as_not_taken(self):
        self.and_the_hormone_replacement_therapy_is_displayed("Not taking HRT")

    @allure.step("And the hormone replacement therapy is displayed as 'Taking HRT'")
    def and_the_hormone_replacement_therapy_is_displayed_as_taken(self):
        self.and_the_hormone_replacement_therapy_is_displayed(
            "Currently taking HRT Started: August 2024"
        )

    @allure.step("And the hormone replacement therapy is displayed")
    def and_the_hormone_replacement_therapy_is_displayed(self, expected_text):
        heading = self.page.get_by_role("heading").filter(has_text="Other information")
        section = self.page.locator(".nhsuk-card").filter(has=heading)
        expect(section).to_be_visible()

        row = section.locator(
            ".nhsuk-summary-list__row", has_text="Hormone replacement therapy (HRT)"
        )
        value = row.locator(".nhsuk-summary-list__value")
        expect(value).to_have_text(expected_text)
