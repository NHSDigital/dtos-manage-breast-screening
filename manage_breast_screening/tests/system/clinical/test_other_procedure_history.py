from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)

from ..system_test_setup import SystemTestCase


class TestRecordingOtherProcedure(SystemTestCase):
    def test_adding_and_changing_other_procedure(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()
        self.when_i_click_on_add_other_procedure()
        self.then_i_see_the_add_other_procedure_form()

        self.when_i_click_save()
        self.then_i_see_validation_error_for_missing_procedure()

        self.when_i_select_breast_reduction()
        self.and_i_add_procedure_year()
        self.and_i_add_additional_details()
        self.and_i_click_save()
        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_other_procedure_is_listed()
        self.and_the_message_says_other_procedure_added()

        self.when_i_click_change()
        self.then_i_see_the_edit_other_procedure_form()
        self.when_i_select_nipple_correction()
        self.and_i_click_save()
        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_other_procedure_is_updated()
        self.and_the_message_says_other_procedure_updated()

    def test_accessibility(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()
        self.when_i_click_on_add_other_procedure()
        self.then_the_accessibility_baseline_is_met()

    def and_there_is_an_appointment(self):
        self.participant = ParticipantFactory(first_name="Janet", last_name="Williams")
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

    def when_i_click_on_add_other_procedure(self):
        self.page.get_by_text("Add other procedure history").click()

    def then_i_see_the_add_other_procedure_form(self):
        expect(self.page.get_by_text("Add details of other procedures")).to_be_visible()
        self.assert_page_title_contains("Details of the other procedure")

    def then_i_see_validation_error_for_missing_procedure(self):
        self.expect_validation_error(
            error_text="Select the procedure",
            fieldset_legend="Procedure",
            field_label="Breast reduction",
        )

    def when_i_select_breast_reduction(self):
        self.page.get_by_label("Breast reduction", exact=True).click()
        self.page.locator("#id_breast_reduction_details").fill(
            "Reason for breast reduction surgery"
        )

    def and_i_add_procedure_year(self):
        self.page.get_by_label("Year of procedure (optional)", exact=True).fill("2000")

    def and_i_add_additional_details(self):
        self.page.get_by_label("Additional details (optional)", exact=True).fill(
            "additional details for test of other procedure"
        )

    def and_i_click_save(self):
        self.page.get_by_text("Save").click()

    when_i_click_save = and_i_click_save

    def then_i_am_back_on_the_medical_information_page(self):
        self.expect_url("mammograms:record_medical_information", pk=self.appointment.pk)

    def and_the_other_procedure_is_listed(self):
        key = self.page.locator(
            ".nhsuk-summary-list__key",
            has=self.page.get_by_text("Other procedure history", exact=True),
        )
        row = self.page.locator(".nhsuk-summary-list__row").filter(has=key)
        expect(row).to_contain_text("Breast reduction")
        expect(row).to_contain_text("Reason for breast reduction surgery")
        expect(row).to_contain_text("2000")
        expect(row).to_contain_text("additional details for test of other procedure")

    def and_the_message_says_other_procedure_added(self):
        alert = self.page.get_by_role("alert")

        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text("Details of other procedure added")

    def then_i_see_the_edit_other_procedure_form(self):
        expect(self.page.get_by_text("Edit details of other procedure")).to_be_visible()
        self.assert_page_title_contains("Details of the other procedure")

    def when_i_click_change(self):
        self.page.get_by_text("Change other procedure item").click()

    def when_i_select_nipple_correction(self):
        self.page.get_by_label("Nipple correction", exact=True).click()
        self.page.locator("#id_nipple_correction_details").fill(
            "Reason for nipple correction surgery"
        )

    def and_the_other_procedure_is_updated(self):
        key = self.page.locator(
            ".nhsuk-summary-list__key",
            has=self.page.get_by_text("Other procedure history", exact=True),
        )
        row = self.page.locator(".nhsuk-summary-list__row").filter(has=key)
        expect(row).to_contain_text("Nipple correction")
        expect(row).to_contain_text("Reason for nipple correction surgery")
        expect(row).to_contain_text("2000")
        expect(row).to_contain_text("additional details for test of other procedure")

    def and_the_message_says_other_procedure_updated(self):
        alert = self.page.get_by_role("alert")

        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text("Details of other procedure updated")
