from datetime import date

import time_machine
from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.core.utils.string_formatting import format_nhs_number
from manage_breast_screening.participants.models import AppointmentStatus
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)

from ..system_test_setup import SystemTestCase


@time_machine.travel(date(2025, 1, 1))
class TestBreastAugmentationHistory(SystemTestCase):
    def test_adding_breast_augmentation(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()
        self.and_i_see_the_appointment_status_bar()
        self.when_i_click_on_breast_implants_or_augmentation()
        self.then_i_see_the_add_breast_augmentation_form()
        self.and_i_see_the_appointment_status_bar()

        self.when_i_click_save_without_entering_details()
        self.then_i_see_validation_errors_for_missing_breast_augmentation_details()

        self.when_i_select_procedures()
        self.and_i_enter_the_procedure_year()
        self.and_i_enter_the_removal_year()
        self.and_i_enter_additional_details()
        self.and_i_click_save_augmentation()
        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_augmentation_is_listed()
        self.and_the_message_says_augmentation_added()

        self.when_i_click_change()
        self.then_i_see_the_edit_breast_augmentation_history_form()
        self.when_i_change_the_additional_details()
        self.and_i_click_save_augmentation()
        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_breast_augmentation_history_is_updated()
        self.and_the_message_says_breast_augmentation_history_updated()

    def test_accessibility(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()
        self.when_i_click_on_breast_implants_or_augmentation()
        self.then_the_accessibility_baseline_is_met()

    def and_there_is_an_appointment(self):
        self.participant = ParticipantFactory(first_name="Janet", last_name="Williams")
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(
            screening_episode=self.screening_episode,
            clinic_slot__clinic__setting__provider=self.current_provider,
            current_status_params={
                "name": AppointmentStatus.STARTED,
                "created_by": self.current_user,
            },
        )

    def and_i_am_on_the_record_medical_information_page(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": self.appointment.pk},
            )
        )

    def when_i_click_on_breast_implants_or_augmentation(self):
        self.page.get_by_role("button").filter(
            has_text="Breast implants or augmentation"
        ).click()

    def then_i_see_the_add_breast_augmentation_form(self):
        expect(
            self.page.get_by_text("Add details of breast implants or augmentation")
        ).to_be_visible()
        self.assert_page_title_contains(
            "Add details of breast implants or augmentation"
        )

    def and_i_see_the_appointment_status_bar(self):
        status_bar = self.page.locator("div.app-status-bar")
        expect(status_bar).to_contain_text(
            format_nhs_number(self.participant.nhs_number)
        )
        expect(status_bar).to_contain_text(self.participant.full_name)

    def then_i_see_validation_errors_for_missing_breast_augmentation_details(self):
        self.expect_validation_error(
            error_text="Select procedures for the right breast",
            fieldset_legend="Right breast",
            field_label="Breast implants (silicone or saline)",
        )
        self.expect_validation_error(
            error_text="Select procedures for the left breast",
            fieldset_legend="Left breast",
            field_label="Breast implants (silicone or saline)",
        )

    def when_i_select_procedures(self):
        self.page.get_by_role("group", name="Right breast").get_by_label(
            "Breast implants (silicone or saline)", exact=True
        ).click()
        self.page.get_by_role("group", name="Left breast").get_by_label(
            "Other augmentation", exact=True
        ).click()

    def and_i_enter_the_procedure_year(self):
        self.page.get_by_label("Year of procedure (optional)", exact=True).fill("2000")

    def and_i_enter_the_removal_year(self):
        self.page.get_by_text("Implants have been removed").click()
        self.page.get_by_label("Year removed (if available)", exact=True).fill("2025")

    def and_i_enter_additional_details(self):
        self.page.get_by_label("Additional details (optional)", exact=True).fill(
            "additional details for test of breast augmentation history"
        )

    def and_i_click_save_augmentation(self):
        self.page.get_by_text("Save").click()

    when_i_click_save_without_entering_details = and_i_click_save_augmentation

    def then_i_am_back_on_the_medical_information_page(self):
        self.expect_url("mammograms:record_medical_information", pk=self.appointment.pk)

    def and_the_augmentation_is_listed(self):
        heading = self.page.get_by_role("heading").filter(
            has_text="Breast implants or augmentation"
        )
        section = self.page.locator("section").filter(has=heading)
        row = section.locator(".app-nested-info__row", has_text="Procedures")
        expect(row).to_contain_text("Right breast Breast implants (silicone or saline)")
        expect(row).to_contain_text("Left breast Other augmentation")

    def and_the_message_says_augmentation_added(self):
        alert = self.page.get_by_role("alert")

        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text("Added breast implants or augmentation")

    def when_i_click_change(self):
        self.page.get_by_text("Change breast implants or augmentation item").click()

    def then_i_see_the_edit_breast_augmentation_history_form(self):
        expect(
            self.page.get_by_text("Edit details of breast implants or augmentation")
        ).to_be_visible()
        self.assert_page_title_contains(
            "Edit details of breast implants or augmentation"
        )

    def when_i_change_the_additional_details(self):
        self.page.get_by_label("Additional details (optional)", exact=True).fill(
            "amended details for test of breast augmentation history"
        )

    def and_the_breast_augmentation_history_is_updated(self):
        heading = self.page.get_by_role("heading").filter(
            has_text="Breast implants or augmentation"
        )
        section = self.page.locator("section").filter(has=heading)
        row = section.locator(".app-nested-info__row", has_text="Additional details")
        expect(row).to_contain_text(
            "amended details for test of breast augmentation history"
        )

    def and_the_message_says_breast_augmentation_history_updated(self):
        alert = self.page.get_by_role("alert")

        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text("Updated breast implants or augmentation")
