from datetime import date

import time_machine
from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.core.utils.string_formatting import format_nhs_number
from manage_breast_screening.participants.models.appointment import AppointmentStatus
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)
from manage_breast_screening.tests.system.system_test_setup import SystemTestCase


@time_machine.travel(date(2025, 1, 1))
class TestRecordingMedicalInformation(SystemTestCase):
    def test_adding_medical_history(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()
        self.and_i_see_the_appointment_status_bar()
        self.and_there_is_no_medical_history()

        self.when_i_click_on_implanted_medical_device()
        self.then_i_see_the_add_a_implanted_medical_device_form()
        self.and_i_see_the_appointment_status_bar()

        self.when_i_click_save_without_entering_details()
        self.then_i_see_validation_errors_for_missing_implanted_medical_device_details()

        self.when_i_select_hickman_line()
        self.and_i_enter_the_procedure_year()
        self.and_i_enter_the_removal_year()
        self.and_i_enter_additional_details()
        self.and_i_click_save()
        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_device_is_listed()
        self.and_the_message_says_device_added()

    def test_changing_medical_history(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()
        self.and_i_see_the_appointment_status_bar()
        self.when_i_click_on_breast_cancer()
        self.then_i_see_the_add_breast_cancer_history_form()

        self.when_i_select_right_breast()
        self.and_i_select_lumpectomy_in_right_breast()
        self.and_i_select_no_surgery_in_left_breast()
        self.and_i_select_no_other_surgery()
        self.and_i_select_no_radiotherapy()
        self.and_i_select_chemotherapy()
        self.and_i_select_a_private_clinic()
        self.and_i_enter_the_details_of_the_private_clinic()
        self.and_i_click_save()
        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_breast_cancer_is_listed()
        self.and_the_message_says_breast_cancer_added()

        self.when_i_click_change_breast_cancer_item()
        self.then_i_see_the_edit_breast_cancer_history_form()
        self.when_i_select_breast_radiotherapy_in_right_breast()
        self.and_i_click_save()
        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_history_item_shows_the_radiotherapy()
        self.and_the_message_says_breast_cancer_history_updated()

    def test_removing_medical_history(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()
        self.and_i_see_the_appointment_status_bar()
        self.when_i_click_on_other_procedures()
        self.then_i_see_the_add_other_procedure_form()
        self.and_i_see_the_appointment_status_bar()

        self.when_i_select_breast_reduction()
        self.and_i_add_procedure_year()
        self.and_i_add_additional_details()
        self.and_i_click_save()
        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_other_procedure_is_listed()
        self.and_the_message_says_other_procedure_added()

        self.when_i_click_change_other_procedures()
        self.then_i_see_the_edit_other_procedure_form()
        self.and_i_click_delete_this_item()
        self.and_i_click_delete_item()
        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_other_procedure_is_gone()

    def test_accessibility(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()
        self.when_i_click_on_breast_cancer()
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

    def when_i_click_on_breast_cancer(self):
        self.page.get_by_role("button").filter(has_text="Breast cancer").click()

    def and_i_see_the_appointment_status_bar(self):
        status_bar = self.page.locator("div.app-status-bar")
        expect(status_bar).to_contain_text(
            format_nhs_number(self.participant.nhs_number)
        )
        expect(status_bar).to_contain_text(self.participant.full_name)

    def when_i_click_on_implanted_medical_device(self):
        self.page.get_by_role("button").filter(
            has_text="Implanted medical device"
        ).click()

    def then_i_see_the_add_a_implanted_medical_device_form(self):
        expect(
            self.page.get_by_text("Add details of implanted medical device")
        ).to_be_visible()
        self.assert_page_title_contains("Add details of implanted medical device")

    def then_i_see_validation_errors_for_missing_implanted_medical_device_details(self):
        self.expect_validation_error(
            error_text="Select the device type",
            fieldset_legend="What device does Janet have?",
            field_label="Cardiac device (such as a pacemaker or ICD)",
        )

    def when_i_select_hickman_line(self):
        self.page.get_by_label("Hickman line", exact=True).click()

    def and_i_enter_the_procedure_year(self):
        self.page.get_by_label("Year of procedure (optional)", exact=True).fill("2000")

    def and_i_enter_the_removal_year(self):
        self.page.get_by_text("Implanted device has been removed").click()
        self.page.get_by_label("Year removed (if available)", exact=True).fill("2025")

    def and_i_enter_additional_details(self):
        self.page.get_by_label("Additional details (optional)", exact=True).fill(
            "additional details for test of implanted medical device history"
        )

    def when_i_click_save_without_entering_details(self):
        self.and_i_click_save()

    def and_the_device_is_listed(self):
        heading = self.page.get_by_role("heading").filter(
            has_text="Implanted medical device"
        )
        section = self.page.locator("section").filter(has=heading)

        row = section.locator(".app-nested-info__row", has_text="Type")
        expect(row).to_contain_text("Hickman line")

        row = section.locator(".app-nested-info__row", has_text="Procedure year")
        expect(row).to_contain_text("Implanted in 2000 (25 years ago)")

        row = section.locator(".app-nested-info__row", has_text="Additional details")
        expect(row).to_contain_text(
            "additional details for test of implanted medical device history"
        )

    def and_the_breast_cancer_is_listed(self):
        heading = self.page.get_by_role("heading").filter(has_text="Breast cancer")
        expect(heading).to_be_attached()

        section = self.page.locator("section").filter(has=heading)
        expect(section).to_be_attached()

        row = section.locator(".app-nested-info__row", has_text="Cancer location")

        expect(row).to_contain_text("Right breast")

    def and_the_message_says_breast_cancer_added(self):
        alert = self.page.get_by_role("alert")

        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text("Added breast cancer")

    def and_the_message_says_device_added(self):
        alert = self.page.get_by_role("alert")

        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text("Added implanted medical device")

    def then_i_see_the_add_breast_cancer_history_form(self):
        expect(self.page.get_by_text("Add details of breast cancer")).to_be_visible()
        self.assert_page_title_contains("Add details of breast cancer")

    def then_i_see_the_edit_breast_cancer_history_form(self):
        expect(self.page.get_by_text("Edit details of breast cancer")).to_be_visible()
        self.assert_page_title_contains("Edit details of breast cancer")

    def when_i_select_right_breast(self):
        fieldset = self.get_fieldset_by_legend("In which breasts was cancer diagnosed?")
        fieldset.get_by_label("Right breast").click()

    def and_i_select_lumpectomy_in_right_breast(self):
        fieldset = self.get_fieldset_by_legend(
            "What procedure have they had in their Right breast (or axilla)?"
        )
        fieldset.get_by_label("Lumpectomy").first.click()

    def and_i_select_no_surgery_in_left_breast(self):
        fieldset = self.get_fieldset_by_legend(
            "What procedure have they had in their Left breast (or axilla)?"
        )
        fieldset.get_by_label("No procedure").last.click()

    def and_i_select_no_other_surgery(self):
        fieldset = self.get_fieldset_by_legend(
            "What other surgery have they had in their Right breast (or axilla)?"
        )
        fieldset.get_by_label("No other surgery").click()

        fieldset = self.get_fieldset_by_legend(
            "What other surgery have they had in their Left breast (or axilla)?"
        )
        fieldset.get_by_label("No other surgery").click()

    def and_i_select_no_radiotherapy(self):
        fieldset = self.get_fieldset_by_legend(
            "What treatment have they had in their Right breast (or axilla)?"
        )
        fieldset.get_by_label("No radiotherapy").click()

        fieldset = self.get_fieldset_by_legend(
            "What treatment have they had in their Left breast (or axilla)?"
        )
        fieldset.get_by_label("No radiotherapy").click()

    def and_i_select_chemotherapy(self):
        fieldset = self.get_fieldset_by_legend("Systemic treatments")
        fieldset.get_by_label("Chemotherapy").click()

    def and_i_select_a_private_clinic(self):
        fieldset = self.get_fieldset_by_legend(
            "Where did surgery and treatment take place?"
        )
        fieldset.get_by_label("At a private clinic in the UK").click()

    def and_i_enter_the_details_of_the_private_clinic(self):
        fieldset = self.get_fieldset_by_legend(
            "Where did surgery and treatment take place?"
        )
        fieldset.get_by_label("Provide details").filter(visible=True).fill("Abc clinic")

    def and_i_click_save(self):
        self.page.get_by_text("Save").click()

    def then_i_am_back_on_the_medical_information_page(self):
        self.expect_url("mammograms:record_medical_information", pk=self.appointment.pk)

    def when_i_click_change_breast_cancer_item(self):
        self.page.get_by_text("Change (breast cancer)").click()

    def when_i_select_breast_radiotherapy_in_right_breast(self):
        fieldset = self.get_fieldset_by_legend(
            "What treatment have they had in their Right breast (or axilla)?"
        )
        fieldset.get_by_label("Breast radiotherapy").click()

    def and_the_history_item_shows_the_radiotherapy(self):
        heading = self.page.get_by_role("heading").filter(has_text="Breast cancer")
        section = self.page.locator("section").filter(has=heading)
        row = section.locator(".app-nested-info__row", has_text="Treatment").first

        expect(row).to_contain_text("Breast radiotherapy")

    def and_the_message_says_breast_cancer_history_updated(self):
        alert = self.page.get_by_role("alert")

        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text("Updated breast cancer")

    def when_i_click_on_other_procedures(self):
        self.page.get_by_role("button").filter(has_text="Other procedures").click()

    def then_i_see_the_add_other_procedure_form(self):
        expect(self.page.get_by_text("Add details of other procedures")).to_be_visible()
        self.assert_page_title_contains("Add details of other procedures")

    def when_i_select_breast_reduction(self):
        self.page.get_by_label("Breast reduction", exact=True).click()
        self.page.locator("#id_breast_reduction_details").fill(
            "Reason for breast reduction surgery"
        )

    def and_i_add_procedure_year(self):
        self.page.get_by_label("Year of procedure (optional)", exact=True).fill("2000")

    def and_i_add_additional_details(self):
        self.page.get_by_label("Additional details (optional)", exact=True).fill(
            "additional details"
        )

    def and_the_other_procedure_is_listed(self):
        heading = self.page.get_by_role("heading").filter(has_text="Other procedures")
        section = self.page.locator("section").filter(has=heading)

        row = section.locator(".app-nested-info__row", has_text="Type")
        expect(row).to_contain_text("Breast reduction")

        row = section.locator(".app-nested-info__row", has_text="Procedure year")
        expect(row).to_contain_text("2000 (25 years ago)")

        row = section.locator(".app-nested-info__row", has_text="Additional details")
        expect(row).to_contain_text("additional details")

    def and_the_message_says_other_procedure_added(self):
        alert = self.page.get_by_role("alert")

        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text("Added other procedures")

    def then_i_see_the_edit_other_procedure_form(self):
        expect(self.page.get_by_text("Edit details of other procedure")).to_be_visible()
        self.assert_page_title_contains("Edit details of other procedures")

    def when_i_click_change_other_procedures(self):
        self.page.get_by_text("Change (other procedures)").click()

    def and_i_click_delete_this_item(self):
        self.page.get_by_text("Delete this item").click()

    def and_i_click_delete_item(self):
        self.page.get_by_text("Delete item").click()

    def and_the_other_procedure_is_gone(self):
        heading = self.page.get_by_role("heading").filter(has_text="Other procedures")
        expect(heading).not_to_be_attached()

    def and_there_is_no_medical_history(self):
        expect(
            self.page.get_by_text("No medical history has been added yet.")
        ).to_be_attached()
